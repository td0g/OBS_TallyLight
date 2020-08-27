# OBS_TallyLight

## Use

### Hardware & Setup

Please see https://td0g.ca/2020/05/27/simple-tally-light-for-obs-studio/

Note - If 2.4GHz WiFi is not available, I would recommend the Raspberry Pi 3B+ (Not the 3B) for 5GHz Wifi.  I haven't found a more affordable solution.

### Configuration

By default, the script will create a new logfile every day.  If you wish to have only one logfile, comment out [line 30](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L30) and uncomment [line 29](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L29).

Set the character that triggers the LED in [line 37](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L37).

Set the websocket password in [line 49](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L49).

## License

Documentation is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)

Software is licensed under a [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt)
