# define the environment name
$envName = "agent"
conda activate $envName
# run streamlit application
cd .\web_gui
streamlit run web.py