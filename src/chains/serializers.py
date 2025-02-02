from abc import abstractmethod

from drf_yasg.utils import swagger_serializer_method
from gnosis.eth.django.serializers import EthereumAddressField
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import Chain, Feature, GasPrice, Wallet


class GasPriceOracleSerializer(serializers.Serializer[GasPrice]):
    type = serializers.ReadOnlyField(default="oracle")
    uri = serializers.URLField(source="oracle_uri")
    gas_parameter = serializers.CharField(source="oracle_parameter")
    gwei_factor = serializers.DecimalField(max_digits=19, decimal_places=9)


class GasPriceFixedSerializer(serializers.Serializer[GasPrice]):
    type = serializers.ReadOnlyField(default="fixed")
    wei_value = serializers.CharField(source="fixed_wei_value")


class GasPriceSerializer(serializers.Serializer[GasPrice]):
    def to_representation(self, instance: GasPrice) -> ReturnDict:
        if instance.oracle_uri and instance.fixed_wei_value is None:
            return GasPriceOracleSerializer(instance).data
        elif instance.fixed_wei_value and instance.oracle_uri is None:
            return GasPriceFixedSerializer(instance).data
        else:
            raise APIException(
                f"The gas price oracle or a fixed gas price was not provided for chain {instance.chain}"
            )


class ThemeSerializer(serializers.Serializer[Chain]):
    text_color = serializers.CharField(source="theme_text_color")
    background_color = serializers.CharField(source="theme_background_color")


class CurrencySerializer(serializers.Serializer[Chain]):
    name = serializers.CharField(source="currency_name")
    symbol = serializers.CharField(source="currency_symbol")
    decimals = serializers.IntegerField(source="currency_decimals")
    logo_uri = serializers.ImageField(use_url=True, source="currency_logo_uri")


class BaseRpcUriSerializer(serializers.Serializer[Chain]):
    authentication = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField(method_name="get_rpc_value")

    @abstractmethod
    def get_authentication(self, obj: Chain) -> str:  # pragma: no cover
        pass

    @abstractmethod
    def get_rpc_value(self, obj: Chain) -> str:  # pragma: no cover
        pass


class RpcUriSerializer(BaseRpcUriSerializer):
    def get_authentication(self, obj: Chain) -> str:
        return obj.rpc_authentication

    def get_rpc_value(self, obj: Chain) -> str:
        return obj.rpc_uri


class SafeAppsRpcUriSerializer(BaseRpcUriSerializer):
    def get_authentication(self, obj: Chain) -> str:
        return obj.safe_apps_rpc_authentication

    def get_rpc_value(self, obj: Chain) -> str:
        return obj.safe_apps_rpc_uri


class BlockExplorerUriTemplateSerializer(serializers.Serializer[Chain]):
    address = serializers.URLField(source="block_explorer_uri_address_template")
    tx_hash = serializers.URLField(source="block_explorer_uri_tx_hash_template")
    api = serializers.URLField(source="block_explorer_uri_api_template")


class FeatureSerializer(serializers.Serializer[Feature]):
    @staticmethod
    def to_representation(instance: Feature) -> str:
        return instance.key


class WalletSerializer(serializers.Serializer[Wallet]):
    @staticmethod
    def to_representation(instance: Wallet) -> str:
        return instance.key


class ChainSerializer(serializers.ModelSerializer[Chain]):
    chain_id = serializers.CharField(source="id")
    chain_name = serializers.CharField(source="name")
    short_name = serializers.CharField()
    rpc_uri = serializers.SerializerMethodField()
    safe_apps_rpc_uri = serializers.SerializerMethodField()
    block_explorer_uri_template = serializers.SerializerMethodField()
    native_currency = serializers.SerializerMethodField()
    transaction_service = serializers.URLField(
        source="transaction_service_uri", default=None
    )
    vpc_transaction_service = serializers.URLField(source="vpc_transaction_service_uri")
    theme = serializers.SerializerMethodField()
    gas_price = serializers.SerializerMethodField()
    ens_registry_address = EthereumAddressField()
    disabled_wallets = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = Chain
        fields = [
            "chain_id",
            "chain_name",
            "short_name",
            "description",
            "l2",
            "rpc_uri",
            "safe_apps_rpc_uri",
            "block_explorer_uri_template",
            "native_currency",
            "transaction_service",
            "vpc_transaction_service",
            "theme",
            "gas_price",
            "ens_registry_address",
            "recommended_master_copy_version",
            "disabled_wallets",
            "features",
        ]

    @staticmethod
    @swagger_serializer_method(serializer_or_field=CurrencySerializer)  # type: ignore[misc]
    def get_native_currency(obj: Chain) -> ReturnDict:
        return CurrencySerializer(obj).data

    @staticmethod
    @swagger_serializer_method(serializer_or_field=ThemeSerializer)  # type: ignore[misc]
    def get_theme(obj: Chain) -> ReturnDict:
        return ThemeSerializer(obj).data

    @staticmethod
    @swagger_serializer_method(serializer_or_field=BaseRpcUriSerializer)  # type: ignore[misc]
    def get_safe_apps_rpc_uri(obj: Chain) -> ReturnDict:
        return SafeAppsRpcUriSerializer(obj).data

    @staticmethod
    @swagger_serializer_method(serializer_or_field=BaseRpcUriSerializer)  # type: ignore[misc]
    def get_rpc_uri(obj: Chain) -> ReturnDict:
        return RpcUriSerializer(obj).data

    @staticmethod
    @swagger_serializer_method(serializer_or_field=BlockExplorerUriTemplateSerializer)  # type: ignore[misc]
    def get_block_explorer_uri_template(obj: Chain) -> ReturnDict:
        return BlockExplorerUriTemplateSerializer(obj).data

    @swagger_serializer_method(serializer_or_field=GasPriceSerializer)  # type: ignore[misc]
    def get_gas_price(self, instance) -> ReturnDict:  # type: ignore[no-untyped-def]
        ranked_gas_prices = instance.gasprice_set.all().order_by("rank")
        return GasPriceSerializer(ranked_gas_prices, many=True).data

    @swagger_serializer_method(serializer_or_field=WalletSerializer)  # type: ignore[misc]
    def get_disabled_wallets(self, instance) -> ReturnDict:  # type: ignore[no-untyped-def]
        disabled_wallets = instance.get_disabled_wallets().order_by("key")
        return WalletSerializer(disabled_wallets, many=True).data

    @swagger_serializer_method(serializer_or_field=FeatureSerializer)  # type: ignore[misc]
    def get_features(self, instance) -> ReturnDict:  # type: ignore[no-untyped-def]
        enabled_features = instance.feature_set.all().order_by("key")
        return FeatureSerializer(enabled_features, many=True).data
