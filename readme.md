#### [Нажмите сюда, чтобы посмотреть на русском](https://github.com/apepenkov/notcoin-client/blob/main/readme_ru.md)

## Guide:

1. Download and install [python](https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe) (make sure to select "add python to path" when installing)

2. Go to https://my.telegram.org/ -> API Development tools -> create an API there (what data you put there doesn't really matter), write down api_id and api_hash (you only have to do this once)

3. Download the zip with bot

4. Create file license.txt and put your key there

5. In folder "configs" create a file (for example, `account1.json` - you can just duplicate `example.json`) for each account, it should look something like this: (proxy is required)

```json
{
"proxy": "http://login:password@ip:port",
"configuration": null
}
```

6. Open `[python](https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe)`, navigate to the folder with the bot

7. Run 
```bash
python configure.py
```
and supply required data
- api_id - from the telegram website, obtained in step 2
- api_hash - from the telegram website, obtained in step 2
- ref - your ref parameter. Empty to leave blank.

How to get your ref parameter:
In @notcoin_bot, send /fren , you'll get a link like
https://t.me/notcoin_bot?start=rp_4220671, the rp_4220671 is the part you need to put

8. run 
```bash
python notcoin_client.py
```
to run the bot