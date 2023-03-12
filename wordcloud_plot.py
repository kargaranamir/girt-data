import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud


"""
Create a wordcloud from body part of IRTs in Markdown format
"""

pattern = r'''(?x)          # set flag to allow verbose regexps
        (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
      | \w+(?:-\w+)*        # words with optional internal hyphens
      | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
      | \.\.\.              # ellipsis
      | [][.,;"'?():_`-]    # these are separate tokens; includes ], [
    '''

tables_csv = pd.read_csv('characteristics_irts_markdown.csv', index_col='IRT_full_name')

tables_csv = tables_csv[tables_csv['body'].notna()]


all_body_txt_list = tables_csv['body'].tolist()
all_body_txt = ' '.join(all_body_txt_list)
wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                min_font_size = 10,
                regexp = pattern,
                min_word_length=2).generate(all_body_txt)
plt.figure(figsize = (8, 8), facecolor = None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad = 0)
 
plt.show()
plt.savefig('wordcloud.png') # wordcloud.pdf