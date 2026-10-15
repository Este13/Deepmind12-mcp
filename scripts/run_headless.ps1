param([Parameter(Mandatory, Position = 0)][string]$Script, [Parameter(ValueFromRemainingArguments)][string[]]$ScriptArgs)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not $env:JAVA_HOME) { throw 'JAVA_HOME (JDK 21+) doit etre defini' }
& "$root\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat" "$root\work\ghidra_proj" DM12 `
    -process DeepMind12 -noanalysis -readOnly -scriptPath "$root\scripts" -postScript $Script @ScriptArgs `
    -log "$root\work\headless.log"
