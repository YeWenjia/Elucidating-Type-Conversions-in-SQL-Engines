To run tests:

```
python -m pytest test/spider/test_spider_folders.py -v
```

To run tests with prints:

```
python -m pytest test/spider/test_spider_folders.py -v -s
```

To run one particular test:

```
python -m pytest test/spider/test_spider_folders.py -k "activity_1/0002" -v -s
```

To run one particular test against a single engine, prefix the filter with the engine name (`postgres`, `mysql`, `sqlite`, `mssql`, `oracle`). Test IDs follow `{engine}_{folder}/{yaml_stem}`:

```
python -m pytest test/spider/test_spider_folders.py -k "mssql_activity_1/0002" -v -s
python -m pytest test/spider/test_spider_folders.py -k "oracle_activity_1/0002" -v -s
```

To run all benchmarks against a single engine, filter with just the engine name:

```
python -m pytest test/spider/test_spider_folders.py -k mssql -v
python -m pytest test/spider/test_spider_folders.py -k oracle -v
```

```
python -m pytest test/spider/test_spider_folders.py -k 'oracle_tracking_share_transactions/0014' -v

```


```
EXHAUSTIVE_QUERIES_FILE=test/exhaustive/corpus/medium.jsonl python -m pytest test/exhaustive/ --tb=line -q
```

