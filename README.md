# flask_api_with_account_template

For debug:
```bash
python3 app.py
```

For production:
```bash
gunicorn -w $WORKERS -t $TIMEOUT -b :$PORT wsgi:app
```
For example:
```bash
gunicorn -w 2 -t 9600 -b :8989 wsgi:app
```
