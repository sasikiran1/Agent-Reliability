# Private setup check only. No model, fault injection, write workload or load test.
$ErrorActionPreference='Stop'
$runStamp=[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff')
$name='ars-shopping-admin-feasibility-'+$runStamp
$dir='data/feasibility/environment-'+$runStamp
New-Item -ItemType Directory -Force $dir | Out-Null
$started=$false
$outcome='setup_error'
try {
    $free=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory
    @{utc=[DateTime]::UtcNow.ToString('o');free_ram_kib=$free;start_threshold_kib=2097152} | ConvertTo-Json | Set-Content "$dir/start-gate.json"
    if ($free -lt 2097152) { $outcome='not_started_resource_gate';throw 'Start gate: less than 2 GiB host RAM available' }
    $image=docker image inspect am1n3e/webarena-verified-shopping_admin:latest | ConvertFrom-Json
    $image | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 "$dir/image.json"
    $pin=$image[0].RepoDigests[0]
    if (-not $pin) { throw 'Missing immutable image digest' }
    # Bind exclusively to loopback. Resource caps are explicit setup interventions.
    $id=docker run -d --name $name --label agent-reliability-study=feasibility --memory 1536m --memory-swap 1536m --cpus 2 --pids-limit 256 -p 127.0.0.1:17780:80 -p 127.0.0.1:17781:8877 $pin
    if ($LASTEXITCODE -ne 0) { throw 'Container launch failed' }
    $started=$true
    $id | Set-Content "$dir/container-id.txt"
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $outcome='health_not_ready_within_setup_budget'
    for ($i=0; $i -lt 20; $i++) {
        $os=Get-CimInstance Win32_OperatingSystem
        $stats=docker stats --no-stream --format '{{json .}}' $name
        $health=$null;$errorText=$null
        $requestClock=[Diagnostics.Stopwatch]::StartNew()
        try { $health=Invoke-RestMethod http://127.0.0.1:17781/status -TimeoutSec 3 } catch { $errorText=$_.Exception.Message }
        $requestClock.Stop()
        @{utc=[DateTime]::UtcNow.ToString('o');elapsed_ms=$clock.ElapsedMilliseconds;free_ram_kib=$os.FreePhysicalMemory;docker_stats=$stats;health=$health;health_request_ms=$requestClock.ElapsedMilliseconds;error=$errorText;live_model=$false;track='controlled_setup'} | ConvertTo-Json -Depth 20 -Compress | Add-Content -Encoding UTF8 "$dir/samples.jsonl"
        if ($os.FreePhysicalMemory -lt 1048576) { $outcome='stopped_host_ram_below_1gib';break }
        if ($clock.Elapsed.TotalSeconds -ge 90) { break }
        Start-Sleep -Seconds 1
    }
    # Save a single read-only site request; redirects are bounded and recorded.
    if ($outcome -ne 'stopped_host_ram_below_1gib') {
        try {
            $r=Invoke-WebRequest http://127.0.0.1:17780/admin -UseBasicParsing -MaximumRedirection 3 -TimeoutSec 10
            @{status=$r.StatusCode;headers=$r.Headers;content_length=$r.RawContentLength} | ConvertTo-Json -Depth 8 | Set-Content "$dir/site-response.json"
            $outcome='site_responded_readiness_requires_review'
        } catch { $_.Exception.Message | Set-Content "$dir/site-error.txt" }
    }
} catch { $_.Exception.Message | Set-Content "$dir/setup-error.txt" }
finally {
    try {
        if ($started) {
            try {
                docker inspect $name | Set-Content -Encoding UTF8 "$dir/container-final.json"
                # Native stderr warnings must not prevent the stop in finally.
                $savedPreference=$ErrorActionPreference
                try {
                    $ErrorActionPreference='Continue'
                    docker logs --tail 200 $name 1> "$dir/container-stdout.log" 2> "$dir/container-stderr.log"
                } finally { $ErrorActionPreference=$savedPreference }
            } finally {
                docker stop --timeout 10 $name | Set-Content "$dir/stop.txt"
                if ($LASTEXITCODE -ne 0) { throw 'Study container stop failed; explicit cleanup required' }
                docker inspect $name --format '{{json .State}}' | Set-Content "$dir/stopped-state.json"
            }
        }
    } finally {
        @{utc=[DateTime]::UtcNow.ToString('o');outcome=$outcome;live_model=$false;model_calls=0;benchmark_tasks_attempted=0;ram_cap_mib=1536;cpu_cap=2;host_stop_threshold_kib=1048576;ports='loopback only';container_retained=$started;container_name=$name} | ConvertTo-Json | Set-Content -Encoding UTF8 "$dir/outcome.json"
        Get-Content "$dir/outcome.json"
    }
}
