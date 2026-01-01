import pandas as pd

# טעינת הנתונים שלך (השתמשי בנתיב לקובץ ה-CSV או ה-PKL שלך)
df = pd.read_pickle(r'C:\Users\תמר\Desktop\CasAI\data\ikea_embeddings.pkl')

# הדפסת הקטגוריות
categories = df['item_cat'].unique().tolist()
print("הקטגוריות הקיימות בדאטה שלי הן:")
print(categories)