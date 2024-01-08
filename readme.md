## How to use?

1. Install dependencies
```bash
pip install -r requirements.txt
```


2. copy `example_configuration.json` to `configuration.json` and edit it.

To obtain `api_id` and `api_hash` go to https://my.telegram.org/auth and create an app.

3. Populate `configs` folder, each config should look something like this:

```json
{
  "proxy": "http://user:pass@ip:port",
  "configuration": null
}
```

Where configuration is taken by default from `configuration.json`'s `bot_config`.

4. Put your license key to `license.txt`

5. Run the bot
```bash
python notcoin_client.py
```
