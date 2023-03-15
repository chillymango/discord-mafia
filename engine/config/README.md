# Game Configuration

The game configuration is stored via Excel sheets.

Config Storage Location: https://docs.google.com/spreadsheets/d/1PMiXU_B2eATCXlZuFsEuKFa9KjDCSWdC9ONlQ6OZY6Q/edit?usp=sharing

## Building
Run the following:
```
python engine/config/gen.py
```

This should update the config object from the template.
To use a different template, modify the Sheet ID

## Using the Config
The config should be referenceable by the game.
The game should be made available as a context variable.
