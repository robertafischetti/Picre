"""---------------------------------------------------------------------------------------
 Module: config

 Author = Roberta Fischetti

 Date = 2026-08-06

 Description = Load yaml file and expose settings.
---------------------------------------------------------------------------------------"""

import yaml
import platform
from pathlib import Path
from dataclasses import dataclass


# DATACLASSES ----------------------------------------------------------------------------
""" 
Created several configuration classes for the following benefits:
- Autocomplete;
- Type checking; 
- Readability.

Used a decorator to avoid writing a lot of repetitive code. 
"""
@dataclass
class FFmpegConfig:
    codec: str
    pixel_format: str
    crf: int

@dataclass
class PlayblastConfig:
    folder_pattern: str
    filename_pattern: str
    version_padding: int

@dataclass
class BurninsConfig:
    corner_positions: str
    corner_fields: str

@dataclass
class PlatformConfig:
    ffmpeg_path: str
    font_path: str

@dataclass
class Config:
    ffmpeg: FFmpegConfig
    playblast: PlayblastConfig
    burnins: BurninsConfig
    platform: PlatformConfig


# VARIABLES ------------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# FUNCTIONS ------------------------------------------------------------------------------
def load_config() -> Config:

    with open(CONFIG_PATH) as file:
        raw = yaml.safe_load(file)

    system = platform.system()

    return Config(
        ffmpeg=FFmpegConfig(**raw["ffmpeg"]),
        playblast=PlayblastConfig(**raw["playblast"]),
        burnins=BurninsConfig(**raw["burnins"]),
        platform=PlatformConfig(**raw["platforms"][system]),
    )


# START ------------------------------------------------------------------------------
config = load_config()
