import pandas as pd
from bert_score import score

# Define the function to calculate BERT Score
def calculate_bert_score(reference, prediction):
    """
    Calculates the BERT score between a reference text and a prediction text.

    Args:
        reference (str): The reference text.
        prediction (str): The prediction text.

    Returns:
        float: The BERT score, or 1 if either input is empty.
    """
    if pd.isna(reference) and pd.isna(prediction):  # change
        return 1
    elif pd.isna(reference) or pd.isna(prediction): # change
        return 0
    else:
        P, R, F1 = score([prediction], [reference], lang="en")
        return F1.item()

# Read the excel file
try:
    df_llmind = pd.read_excel("evaluation.xlsx")
except FileNotFoundError:
    print("Error: 'evaluation.xlsx' not found. Please make sure the file exists in the same directory as the script.")
    exit()

# Apply the function to the specified columns for each dataframe
df_llmind['Discussion_BERT'] = df_llmind.apply(lambda row: calculate_bert_score(row['Diagnosis'], row['LLMind']), axis=1)
df_llmind['Diagnosis_BERT'] = df_llmind.apply(lambda row: calculate_bert_score(row['Diagnosis'], row['Diagnosi']), axis=1)
df_llmind['RDF_BERT'] = df_llmind.apply(lambda row: calculate_bert_score(row['RDF'], row['RDF']), axis=1) # Comparing the same column

# Print the BERT scores for each DataFrame
print("LLMind BERT Scores:")
print(df_llmind[['Discussion_BERT', 'Diagnosis_BERT', 'RDF_BERT']].to_markdown(index=False, numalign="left", stralign="left"))
