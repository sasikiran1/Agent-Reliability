param([ValidateSet('qwen3.5:4b','llama3.1:8b')][string]$Model='qwen3.5:4b')
$ErrorActionPreference='Stop'
$id='smoke-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
$dir=Join-Path 'results' $id
New-Item -ItemType Directory -Path $dir | Out-Null
$clock=[Diagnostics.Stopwatch]::StartNew()
function SaveJson($name,$value) { $value | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 (Join-Path $dir $name) }
function Event($kind,$detail) {
    [ordered]@{task_id=$id;track='controlled_setup';live_model=$true;session_id=1;event_id=[guid]::NewGuid().ToString();parent_attempt=$null;retry_source='none';utc=[DateTime]::UtcNow.ToString('o');elapsed_ms=$clock.ElapsedMilliseconds;kind=$kind;detail=$detail} | ConvertTo-Json -Depth 40 -Compress | Add-Content -Encoding UTF8 (Join-Path $dir 'trace.jsonl')
}
function Api($endpoint,$body) { Invoke-RestMethod -Uri ('http://127.0.0.1:11434/api/'+$endpoint) -Method Post -ContentType 'application/json' -Body ($body | ConvertTo-Json -Depth 40 -Compress) -TimeoutSec 180 }
$status='setup_error';$calls=0;$tools=0;$verified=$false;$sample=$null
try {
    $os=Get-CimInstance Win32_OperatingSystem
    if ($os.FreePhysicalMemory -lt 1048576) { throw 'Memory gate: less than 1 GiB free RAM' }
    $loaded=Invoke-RestMethod http://127.0.0.1:11434/api/ps -TimeoutSec 10
    if (@($loaded.models).Count -gt 0) { throw 'A model is already loaded; leave existing sessions untouched' }
    SaveJson 'runtime.json' (Invoke-RestMethod http://127.0.0.1:11434/api/version)
    $tags=Invoke-RestMethod http://127.0.0.1:11434/api/tags
    SaveJson 'model-tags.json' $tags
    $selected=@($tags.models | Where-Object name -eq $Model)
    if ($selected.Count -ne 1) { throw 'Requested model is not installed' }
    $show=Api 'show' @{model=$Model}
    SaveJson 'model-show.json' $show
    if ($show.capabilities -notcontains 'tools') { throw 'Local model does not advertise tools' }
    $sample=Start-Job -ArgumentList (Join-Path (Get-Location).Path "$dir/resources.jsonl") -ScriptBlock {
        param($path)
        while ($true) {
            try {
                $os=Get-CimInstance Win32_OperatingSystem
                $cpu=Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage
                $gpu=nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits
                $ps=Invoke-RestMethod http://127.0.0.1:11434/api/ps -TimeoutSec 3
                @{utc=[DateTime]::UtcNow.ToString('o');free_ram_kib=$os.FreePhysicalMemory;cpu_percent=$cpu;gpu=$gpu;runtime=$ps} | ConvertTo-Json -Depth 12 -Compress | Add-Content -Encoding UTF8 $path
            } catch { @{utc=[DateTime]::UtcNow.ToString('o');error=$_.Exception.Message} | ConvertTo-Json -Compress | Add-Content $path }
            Start-Sleep -Seconds 1
        }
    }
    $schema=@(@{type='function';function=@{name='read_protocol';description='Read the study protocol from disk';parameters=@{type='object';properties=@{};required=@()}}})
    $messages=@(@{role='user';content='Read the study protocol using read_protocol, then summarize its three evidence tracks in one sentence.'})
    for ($i=0;$i -lt 3;$i++) {
        if ($clock.Elapsed.TotalMinutes -gt 10) { throw 'Task deadline exceeded' }
        $request=@{model=$Model;messages=$messages;tools=$schema;stream=$false;keep_alive='2m';options=@{num_ctx=4096;num_predict=512;temperature=0;seed=20261028}}
        Event 'model_request' $request
        $calls++
        $response=Api 'chat' $request
        Event 'model_response' $response
        SaveJson 'loaded-during.json' (Invoke-RestMethod http://127.0.0.1:11434/api/ps -TimeoutSec 10)
        if ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory -lt 1048576) { throw 'Memory gate: less than 1 GiB free RAM after inference' }
        $messages+= $response.message
        if (-not $response.message.tool_calls) { break }
        foreach ($call in $response.message.tool_calls) {
            $tools++
            if ($tools -gt 12) { throw 'Tool budget exceeded' }
            if ($call.function.name -ne 'read_protocol') { throw 'Unknown tool requested' }
            $text=Get-Content -Raw -LiteralPath docs/protocol.md
            $hash=(Get-FileHash docs/protocol.md -Algorithm SHA256).Hash
            Event 'tool_result' @{tool='read_protocol';arguments=$call.function.arguments;committed_effect_ids=@();content=$text;sha256=$hash}
            $verified=$true
            $messages+=@{role='tool';tool_name='read_protocol';content=$text}
        }
    }
    $status=if ($verified) {'tool_read_verified_summary_ungraded'} else {'no_tool_call'}
} catch { Event 'error' @{message=$_.Exception.Message};$status='setup_or_pilot_error' }
finally {
    if ($sample) { Stop-Job $sample; Receive-Job $sample -ErrorAction SilentlyContinue | Out-Null; Remove-Job $sample }
    try { Api 'generate' @{model=$Model;keep_alive=0} | Out-Null } catch { Event 'unload_error' $_.Exception.Message }
    $row=[pscustomobject]@{task_id=$id;track='controlled_setup';model=$Model;status=$status;model_calls=$calls;tool_calls=$tools;tool_read_verified=$verified;duration_ms=$clock.ElapsedMilliseconds;harm_assessed=$false;duplicate_effects=$null;natural_recovery='not observed';context_truncation='unknown';summary_correctness='ungraded'}
    $row | Export-Csv (Join-Path $dir 'result.csv') -NoTypeInformation
    $row | Export-Csv results/results.csv -Append -NoTypeInformation
    $row | Format-List
}
