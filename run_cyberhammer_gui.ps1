# Check if conda is installed
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Error "Conda is not installed. Please install Conda first."
    exit 1
}

$envName = "agent"
$envExists = conda info --envs | Select-String -Pattern "^\s*$envName\s*"

if ($envExists) {
    Write-Output "Environment '$envName' exists. Activating..."
    conda activate $envName
}
else {
    Write-Output "Environment '$envName' does not exist. Please Creating and installing dependencies manually."
    conda create -n $envName python=3.11
    conda activate $envName
    if (Test-Path requirements.txt) {
        pip install -r requirements.txt
    }
    else {
        Write-Error "requirements.txt not found. Please provide the dependencies file."
        exit 1
    }
}

# run streamlit application
streamlit run main.py