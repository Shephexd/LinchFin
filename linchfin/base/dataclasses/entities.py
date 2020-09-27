from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from typing import List, Dict, OrderedDict as OrderedDictType
from uuid import uuid4
import pandas as pd

from .value_types import Weight, AssetId, AssetCode


@dataclass
class Entity:
    def __post_init__(self):
        self.extra = OrderedDict()

    def __getattr__(self, item):
        try:
            return self.extra[item]
        except KeyError as e:
            raise AttributeError(f"{self.__class__.__name__} objects has no attribute {item}")


@dataclass
class AssetClass(Entity):
    asset_class_id: str = field(default_factory=uuid4)
    asset_class_name: str = field(default='')


@dataclass
class Asset(Entity):
    asset_id: AssetId = field(default_factory=uuid4)
    code: str = field(default='')
    asset_class: AssetClass = field(default_factory=AssetClass)


@dataclass
class AssetUniverse(Entity):
    universe_id: str = field(default_factory=uuid4)
    assets: OrderedDictType[AssetId, Asset] = field(default_factory=OrderedDict)
    asset_code_map: OrderedDictType = field(init=False)

    def __post_init__(self):
        if isinstance(self.assets, list):
            asset_dic = OrderedDict()
            for _asset in self.assets:
                asset_dic[_asset.asset_id] = _asset
            self.assets = asset_dic
        elif isinstance(self.assets, OrderedDict):
            pass
        else:
            raise TypeError("Unsupported Assets to initialize universe")
        self.asset_code_map = OrderedDict()
        for asset_id, _asset in self.assets.items():
            self.asset_code_map[_asset.code] = asset_id

    @property
    def symbols(self):
        return [_asset.code for _asset in self.assets.values()]

    def get_asset(self, code: AssetCode) -> Asset:
        asset_id = self.get_asset_id(code=code)
        return self.assets[asset_id]

    def get_asset_id(self, code: AssetCode) -> AssetId:
        code = str(code)
        return self.asset_code_map[code]

    def append(self, asset: Asset):
        self.assets[asset.asset_id] = asset
        self.asset_code_map[asset.code] = asset.asset_id

    def pop(self, asset: str or Asset):
        if isinstance(asset, Asset):
            self.assets.pop(asset.asset_id)
        else:
            self.assets.pop(asset)
        self.asset_code_map.pop(asset.code)


@dataclass
class Cluster(Entity):
    name: str = field(default='')
    elements: List = field(default_factory=list)
    d: float = field(default=0)
    size: int = field(default=0)


@dataclass
class Portfolio(Entity):
    portfolio_id: str = field(default_factory=uuid4)
    _weights: Dict[AssetCode, Weight] = field(default_factory=dict)
    asset_universe: AssetUniverse = field(default_factory=AssetUniverse)

    @property
    def weights(self):
        return self._weights

    @property
    def sector_weights(self):
        _sector_weights = defaultdict(Weight)
        for k, v in self.weights.items():
            _asset = self.asset_universe.get_asset(code=k)
            _sector_weights[_asset.asset_class.asset_class_name] += v
        return _sector_weights

    def set_weights(self, weights: Dict[AssetCode, Weight] or pd.Series):
        for _asset_code, _w in weights.items():
            if _asset_code in self._weights:
                raise KeyError(f"asset name is conflicted, {_asset_code}")

            _asset = self.asset_universe.get_asset(code=_asset_code)
            self._weights[_asset.code] = Weight(_w)

    def round(self, weights, points=2):
        _rounded_weights = OrderedDict()
        for k, v in weights.items():
            _rounded_weights[k] = round(v, points)
        if self.validate(weights=_rounded_weights):
            return _rounded_weights
        else:
            delta = 1 - sum(_rounded_weights.values())
            return delta

    def is_valid(self):
        return self.validate(weights=self.weights)

    def validate(self, weights):
        if not round(sum(weights.values()), 4) == 1.0:
            return False
        return True

    def show_summary(self):
        print(f"Universe ID: {self.asset_universe.universe_id}")
        asset_class_map = defaultdict(list)
        asset_class_weights = defaultdict(Weight)
        for _asset_id, _asset in self.asset_universe.assets.items():
            asset_class_map[_asset.asset_class.asset_class_name].append(
                _asset
            )
            asset_class_weights[_asset.asset_class.asset_class_name] += self.weights[_asset.code]

        for _asset_class_name, assets in asset_class_map.items():
            print(f"AssetClass({_asset_class_name}): weights={asset_class_weights[_asset_class_name]},"
                  f" asset_codes={[_asset.code for _asset in assets]}")
        return asset_class_weights
