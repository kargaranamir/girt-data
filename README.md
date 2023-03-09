# GIRT-Data


## Crawler
Modify `username`, `personal_token` and your `target_repos` then run crawler.py.

```python
python3 crawler.py
```

## GIRT-Data Import

### Pandas

```Python

df_repo = pd.read_csv('CHARACTERISTICS_REPO.csv', index_col='full_name')

df_irt_markdown = pd.read_csv('CHARACTERISTICS_IRTS_MARKDOWN.csv', index_col='IRT_full_name')

df_irt_yaml = pd.read_csv('CHARACTERISTICS_IRTS_YAML.csv', index_col='IRT_full_name')

```
