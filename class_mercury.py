import uuid
from datetime import timedelta, datetime
from uuid import UUID
from class_settings import Settings as JS
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings, xsd
from zeep import Plugin
from zeep.transports import Transport


class SOAPLogging(Plugin):
    def ingress(self, envelope, http_headers, operation):
        txt = str(etree.tostring(envelope)).replace('\\n', '')
        print(txt)
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        txt = str(etree.tostring(envelope)).replace('\\n', '')
        print(txt)
        return envelope, http_headers


class MercuryConnection:
    def __init__(self, login, password, use_plugin=False):
        self.__login = login
        self.__password = password
        self.__session = Session()
        self.__session.auth = HTTPBasicAuth(self.__login, self.__password)
        self.__settings = Settings(strict=False, xml_huge_tree=True)
        self.__wsdl = {
            'ProductionRequest':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/ams-mercury-g2b.service_v2.1_production.wsdl',
            'EnterpriseService':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/EnterpriseService_v2.1_production.wsdl',
            'IkarService':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/IkarService_v2.1_production.wsdl',
            'DictionaryService':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/DictionaryService_v2.1_production.wsdl',
            'ProductService':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/ProductService_v2.1_production.wsdl',
            'RegionalizationService':
                'http://api.vetrf.ru/schema/platform/services/2.1-RC-last/RegionalizationService_v2.1_production.wsdl'
        }
        self.__client = None
        self.__use_plugin = use_plugin

    def connect(self, service_name):
        try:
            if self.__wsdl.get(service_name, None) is not None:
                if self.__use_plugin:
                    self.__client = Client(wsdl=self.__wsdl[service_name], settings=self.__settings,
                                           transport=Transport(session=self.__session), plugins=[SOAPLogging()])
                else:
                    self.__client = Client(wsdl=self.__wsdl[service_name], settings=self.__settings,
                                           transport=Transport(session=self.__session))
                # Заменяем пространства имен, если нашли их.
                self.__client.set_ns_prefix("soap-env", "http://schemas.xmlsoap.org/soap/envelope/")
                self.__client.set_ns_prefix("xs", "http://www.w3.org/2001/XMLSchema")
                self.__client.set_ns_prefix("bs", "http://api.vetrf.ru/schema/cdm/base")
                self.__client.set_ns_prefix("app", "http://api.vetrf.ru/schema/cdm/application")
                self.__client.set_ns_prefix("argc", "http://api.vetrf.ru/schema/cdm/argus/common")
                self.__client.set_ns_prefix("vetd", "http://api.vetrf.ru/schema/cdm/mercury/vet-document/v2")
                self.__client.set_ns_prefix("ent", "http://api.vetrf.ru/schema/cdm/cerberus/enterprise")
                self.__client.set_ns_prefix("argpr", "http://api.vetrf.ru/schema/cdm/argus/production")
                self.__client.set_ns_prefix("shp", "http://api.vetrf.ru/schema/cdm/argus/shipment")
                self.__client.set_ns_prefix("ikar", "http://api.vetrf.ru/schema/cdm/ikar")
                self.__client.set_ns_prefix("wd", "http://api.vetrf.ru/schema/cdm/application/ws-definitions")
                self.__client.set_ns_prefix("wb", "http://api.vetrf.ru/schema/cdm/base/ws-definitions")
                self.__client.set_ns_prefix("wr", "http://api.vetrf.ru/schema/cdm/registry/ws-definitions/v2")
                self.__client.set_ns_prefix("merc", "http://api.vetrf.ru/schema/cdm/mercury/g2b/applications/v2")
                self.__client.set_ns_prefix("dt", "http://api.vetrf.ru/schema/cdm/dictionary/v2")
                return self.__client
            else:
                return None
        except Exception as E:
            print(f'error:{E}')
            return None

    @property
    def client(self):
        return self.__client

    @staticmethod
    def new_guid():
        return uuid.uuid4()

    @staticmethod
    def check_guid(guid):
        try:
            t = UUID(guid)
            if type(t) == UUID:
                return True
            else:
                return False
        except Exception as E:
            return False

    @staticmethod
    def combine_args(in_dict, key_name="default", key_value=None):
        if key_value is not None:
            if type(key_value) == dict:
                if len(key_value) > 0:
                    in_dict[key_name] = key_value
            else:
                in_dict[key_name] = key_value
        return in_dict


class MercuryDictionary(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('DictionaryService')

    @property
    def service(self):
        return self.__link.service

    def get_disease_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetDiseaseByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_disease_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetDiseaseByGuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_disease_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                 end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetDiseaseChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_diseases_list(self, count=100, offset=0):
        try:
            return self.service.GetDiseaseList({'count': count, 'offset': offset})
        except Exception as E:
            return {'error': E}

    def get_purpose_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetPurposeByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_purpose_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetPurposeByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_purpose_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                 end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetPurposeChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_purpose_list(self, count=100, offset=0):
        try:
            return self.service.GetPurposeList({'count': count, 'offset': offset})
        except Exception as E:
            return {'error': E}

    def get_research_method_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetResearchMethodByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_research_method_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetResearchMethodByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_research_method_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                         end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetResearchMethodChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_research_method_list(self, count=100, offset=0):
        try:
            return self.service.GetResearchMethodList({'count': count, 'offset': offset})
        except Exception as E:
            return {'error': E}

    def get_unit_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetUnitByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_unit_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetUnitByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_unit_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                              end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetUnitChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_unit_list(self, count=100, offset=0):
        try:
            return self.service.GetUnitList({'count': count, 'offset': offset})
        except Exception as E:
            return {'error': E}


class MercuryProduct(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('ProductService')

    @property
    def service(self):
        return self.__link.service

    def get_product_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetProductByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_product_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetProductByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_product_by_type_list(self, count=100, offset=0, product_type=1):
        try:
            return self.service.GetProductByTypeList({'count': count, 'offset': offset}, productType=product_type)
        except Exception as E:
            return {'error': E}

    def get_product_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                 end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetProductChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_product_item_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetProductItemByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_product_item_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetProductItemByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_product_item_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                      end_date=datetime.now(), business_entity=None, enterprise=None, producer=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            super().combine_args(args, 'businessEntity', business_entity)
            super().combine_args(args, 'enterprise', enterprise)
            super().combine_args(args, 'producer', producer)
            return self.service.GetProductItemChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_product_item_list(self, count=100, offset=0, product_type=1, product=None, sub_product=None,
                              business_entity=None,
                              enterprise=None, producer=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'productType', product_type)
            super().combine_args(args, 'product', product)
            super().combine_args(args, 'subProduct', sub_product)
            super().combine_args(args, 'businessEntity', business_entity)
            super().combine_args(args, 'enterprise', enterprise)
            super().combine_args(args, 'producer', producer)
            return self.service.GetProductItemList(**args)
        except Exception as E:
            return {'error': E}

    def get_sub_product_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetSubProductByGuid(guid)
            else:
                return {'error': 'Invalid guid.'}
        except Exception as E:
            return {'error': E}

    def get_sub_product_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetSubProductByUuid(uuid)
            else:
                return {'error': 'Invalid uuid.'}
        except Exception as E:
            return {'error': E}

    def get_sub_product_by_product_list(self, count=100, offset=0, product_guid=''):
        try:
            if super().check_guid(product_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'productGuid', product_guid)
                return self.service.GetSubProductByProductList(**args)
            else:
                return {'error': 'invalid product guid'}
        except Exception as E:
            return {'error': E}

    def get_sub_product_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                     end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetSubProductChangesList(**args)
        except Exception as E:
            return {'error': E}


class MercuryRegionalization(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('RegionalizationService')

    @property
    def service(self):
        return self.__link.service

    def get_actual_r13n_region_status_list(self, count=100, offset=0, disease=None, r13n_zone=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'disease', disease)
            super().combine_args(args, 'r13nZone', r13n_zone)
            return self.service.GetActualR13nRegionStatusList(**args)
        except Exception as E:
            return {'error': E}

    def get_actual_r13n_shipping_rule_list(self, count=100, offset=0, disease=None, product_type=None, product=None,
                                           sub_product=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'disease', disease)
            super().combine_args(args, 'productType', product_type)
            super().combine_args(args, 'product', product)
            super().combine_args(args, 'subProduct', sub_product)
            return self.service.GetActualR13nShippingRuleList(**args)
        except Exception as E:
            return {'error': E}

    def get_r13n_condition_list(self, count=100, offset=0, disease=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'disease', disease)
            return self.service.GetR13nConditionList(**args)
        except Exception as E:
            return {'error': E}


class MercuryEnterprise(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('EnterpriseService')

    @property
    def service(self):
        return self.__link.service

    def get_activity_location_list(self, count=100, offset=0, business_entity=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'businessEntity', business_entity)
            return self.service.GetR13nConditionList(**args)
        except Exception as E:
            return {'error': E}

    def get_business_entity_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetBusinessEntityByGuid(guid)
            else:
                return {'error': 'Incorrect guid.'}
        except Exception as E:
            return {'error': E}

    def get_business_entity_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetBusinessEntityByUuid(uuid)
            else:
                return {'error': 'Incorrect uuid.'}
        except Exception as E:
            return {'error': E}

    def get_business_entity_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                         end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetBusinessEntityChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_business_entity_list(self, count=100, offset=0, business_entity=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'businessEntity', business_entity)
            return self.service.GetBusinessEntityList(**args)
        except Exception as E:
            return {'error': E}

    def get_business_member_by_gln(self, global_id=None):
        try:
            args = {}
            super().combine_args(args, 'globalID', global_id)
            return self.service.GetBusinessMemberByGLN(**args)
        except Exception as E:
            return {'error': E}

    def get_enterprise_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetEnterpriseByGuid(guid)
            else:
                return {'error': 'Incorrect guid.'}
        except Exception as E:
            return {'error': E}

    def get_enterprise_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetEnterpriseByUuid(uuid)
            else:
                return {'error': 'Incorrect uuid.'}
        except Exception as E:
            return {'error': E}

    def get_foreign_enterprise_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                            end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetForeignEnterpriseChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_foreign_enterprise_list(self, count=100, offset=0, enterprise_group=None, enterprise=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'enterpriseGroup', enterprise_group)
            super().combine_args(args, 'enterprise', enterprise)
            return self.service.GetForeignEnterpriseList(**args)
        except Exception as E:
            return {'error': E}

    def get_russian_enterprise_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                            end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetRussianEnterpriseChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_russian_enterprise_list(self, count=100, offset=0, enterprise=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'enterprise', enterprise)
            return self.service.GetRussianEnterpriseList(**args)
        except Exception as E:
            return {'error': E}


class MercuryIkarService(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('IkarService')

    @property
    def service(self):
        return self.__link.service

    def find_locality_list_by_name(self, count=100, offset=0, region_guid=None, pattern=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'regionGuid', region_guid)
            super().combine_args(args, 'pattern', pattern)
            return self.service.FindLocalityListByName(**args)
        except Exception as E:
            return {'error': E}

    def find_street_list_by_name(self, count=100, offset=0, locality_guid=None, pattern=None):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'localityGuid', locality_guid)
            super().combine_args(args, 'pattern', pattern)
            return self.service.FindStreetListByName(**args)
        except Exception as E:
            return {'error': E}

    def get_all_country_list(self, count=100, offset=0):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            return self.service.GetAllCountryList(**args)
        except Exception as E:
            return {'error': E}

    def get_country_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetCountryByGuid(guid)
            else:
                return {'error': 'Incorrect guid.'}
        except Exception as E:
            return {'error': E}

    def get_country_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetCountryByUuid(uuid)
            else:
                return {'error': 'Incorrect uuid.'}
        except Exception as E:
            return {'error': E}

    def get_country_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                 end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetCountryChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_district_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetDistrictByGuid(guid)
            else:
                return {'error': 'Incorrect guid.'}
        except Exception as E:
            return {'error': E}

    def get_district_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetDistrictByUuid(uuid)
            else:
                return {'error': 'Incorrect uuid.'}
        except Exception as E:
            return {'error': E}

    def get_district_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                  end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetDistrictChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_district_list_by_region(self, count=100, offset=0, region_guid=''):
        try:
            if super().check_guid(region_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'regionGuid', region_guid)
                return self.service.GetDistrictListByRegion(**args)
            else:
                return {'error': 'Incorrect region_guid.'}
        except Exception as E:
            return {'error': E}

    def get_locality_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                  end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetLocalityChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_locality_list_by_district(self, count=100, offset=0, district_guid=''):
        try:
            if super().check_guid(district_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'districtGuid', district_guid)
                return self.service.GetLocalityListByDistrict(**args)
            else:
                return {'error': 'Incorrect district_guid.'}
        except Exception as E:
            return {'error': E}

    def get_locality_list_by_locality(self, count=100, offset=0, locality_guid=''):
        try:
            if super().check_guid(locality_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'localityGuid', locality_guid)
                return self.service.GetLocalityListByLocality(**args)
            else:
                return {'error': 'Incorrect locality_guid.'}
        except Exception as E:
            return {'error': E}

    def get_locality_list_by_region(self, count=100, offset=0, region_guid=''):
        try:
            if super().check_guid(region_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'regionGuid', region_guid)
                return self.service.GetLocalityListByRegion(**args)
            else:
                return {'error': 'Incorrect region_guid.'}
        except Exception as E:
            return {'error': E}

    def get_region_by_guid(self, guid=''):
        try:
            if super().check_guid(guid):
                return self.service.GetRegionByGuid(guid)
            else:
                return {'error': 'Incorrect guid.'}
        except Exception as E:
            return {'error': E}

    def get_region_by_uuid(self, uuid=''):
        try:
            if super().check_guid(uuid):
                return self.service.GetRegionByUuid(uuid)
            else:
                return {'error': 'Incorrect uuid.'}
        except Exception as E:
            return {'error': E}

    def get_region_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetRegionChangesList(**args)
        except Exception as E:
            return {'error': E}

    def get_region_list_by_country(self, count=100, offset=0, country_guid=''):
        try:
            if super().check_guid(country_guid):
                args = {}
                super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
                super().combine_args(args, 'countryGuid', country_guid)
                return self.service.GetRegionListByCountry(**args)
            else:
                return {'error': 'Incorrect country_guid.'}
        except Exception as E:
            return {'error': E}

    def get_street_changes_list(self, count=100, offset=0, begin_date=datetime.now() - timedelta(2),
                                end_date=datetime.now()):
        try:
            args = {}
            super().combine_args(args, 'listOptions', {'count': count, 'offset': offset})
            super().combine_args(args, 'updateDateInterval', {'beginDate': begin_date, 'endDate': end_date})
            return self.service.GetStreetChangesList(**args)
        except Exception as E:
            return {'error': E}


class MercuryProductionService(MercuryConnection):
    def __init__(self, login, password, use_plugin=False):
        super().__init__(login, password, use_plugin)
        self.__link = super().connect('ProductionRequest')
        self.__api_key = 'API_KEY_HERE'
        self.__initiator = 'WS_USERNAME_HERE'
        self.__issuer_id = uuid.uuid4()
        self.__local_transaction_id = uuid.uuid4()

    @property
    def link(self):
        return self.__link

    @property
    def service(self):
        return self.__link.service

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, value):
        """
        Специальный код, который идентифицирует учетную запись пользователя и позволяет веб-сервису получить доступ к информации о хозяйствующем субъекте и обслуживаемых предприятиях, к которым данный пользователь относится.
        """
        self.__api_key = value

    @property
    def initiator(self):
        return self.__initiator

    @initiator.setter
    def initiator(self, value):
        """
            Пользователь, зарегистрированный в системе Меркурий и инициирующий запрос к шлюзу.
            Является ответственным за выполнение бизнес-операции.
            Здесь потребуется логин ветврача или пользователя ХС.
            Логин для базовой аутентификации не подойдёт.
        """
        self.__initiator = value

    @property
    def issuer_id(self):
        return self.__issuer_id

    @issuer_id.setter
    def issuer_id(self, value):
        """
        Идентификатор хозяйствующего субъекта от имени которого происходит обращение к Ветис.API.
        Указанный хозяйствующий субъект должен быть одним из хозяйствующих субъектов, обслуживаемых данной программной системой.
        Перечень обслуживаемых программной системой хозяйствующих субъектов устанавливается при предоставлении доступа к Ветис.API.
        """
        if type(value) == str:
            self.__issuer_id = UUID(value)
        else:
            self.__issuer_id = value

    @property
    def local_transaction_id(self):
        """
            Хранит уникальный идентификатор заявки в системе отправителя.
        """
        return self.__local_transaction_id

    @property
    def new_local_transaction_id(self):
        """
            Генерирует новый уникальный идентификатор заявки для системы отправителя.
        """
        self.__local_transaction_id = uuid.uuid4()
        return self.__local_transaction_id

    def submit_application_request(self, application_method=None):
        """Отправиь заявку в систему ФГИС Меркурий

        :param application_method: Данные, которые необходимо обернуть и отправить.

        """
        try:
            args = {}
            self.combine_args(args, 'serviceId', 'mercury-g2b.service:2.1')
            self.combine_args(args, 'issuerId', self.issuer_id)
            self.combine_args(args, 'issueDate', datetime.now())
            self.combine_args(args, 'data', application_method)
            app = self.client.get_element('ns2:application')
            return self.service.submitApplicationRequest(apiKey=self.api_key, application=app(**args))
        except Exception as E:
            return {'error': E}

    def receive_application_result(self, application_id=None):
        """Получить данные по идентификатору заявки.

        :param application_id: Идентификатор заявки.

        :rtype: Application

        """
        try:
            if type(application_id) == str:
                application_id = UUID(application_id)
            args = {}
            self.combine_args(args, 'apiKey', self.__api_key)
            self.combine_args(args, 'issuerId', self.issuer_id)
            self.combine_args(args, 'applicationId', application_id)
            return self.service.receiveApplicationResult(**args)
        except Exception as E:
            return {'error': E}

    def get_stock_entry_list_request(self, enterprise_guid='', count=100, offset=0, full_len=False):
        """Операция предназначена для получения актуального списка записей складского журнала.

        :param enterprise_guid: Идентификатор предприятия, по которому производится поиск записи.
        :param count: Максимальное запрашиваемое количество объектов в списке.
        :param offset: Номер элемента, по которому осуществляется смещение первого элемента списка.
        :param full_len: Фильтр по объему записей складского журнала. (По умолчанию отбирает только записи с остатком больше 0)

        Подробно: https://help.vetrf.ru/wiki/GetStockEntryListOperation_v2.0"""
        request = self.link.get_element('ns4:getStockEntryListRequest')
        args = {}
        self.combine_args(args, 'localTransactionId', self.new_local_transaction_id)
        self.combine_args(args, 'enterpriseGuid', enterprise_guid)
        self.combine_args(args, 'listOptions', {'count': count, 'offset': offset})
        if not full_len:
            self.combine_args(args, 'searchPattern', {'blankFilter': 'NOT_BLANK'})
        self.combine_args(args, 'initiator', {'login': self.initiator})
        return xsd.AnyObject(request, request(**args))

    def get_vet_document_by_uuid_request(self, guid='', enterprise_guid=''):
        """Операция GetVetDocumentByUuidOperation предназначена для получения ветеринарного сопроводительного документа (ВСД) по его уникальному идентификатору.

        :param enterprise_guid: Идентификатор предприятия, по которому производится поиск документа.
        :param guid: Идентификатор ВСД.

        :rtype: xsd.AnyObject

        Подробно: https://help.vetrf.ru/wiki/GetVetDocumentByUuidOperation_v2.0"""
        request = self.link.get_element('ns4:getVetDocumentByUuidRequest')
        args = {}
        self.combine_args(args, 'localTransactionId', uuid.uuid4())
        self.combine_args(args, 'enterpriseGuid', UUID(enterprise_guid))
        self.combine_args(args, 'uuid', UUID(guid))
        self.combine_args(args, 'initiator', {'login': self.initiator})
        return xsd.AnyObject(request, request(**args))


s = JS('settings.json')
mc2 = MercuryProductionService(s.param('auth'), s.param('pass'), use_plugin=False)
mc2.api_key = s.param('api_key')
mc2.initiator = s.param('initiator')
mc2.issuer_id = s.param('issuer_id')
request = mc2.get_stock_entry_list_request('fd3f39fd-01c0-4d02-9f0e-8f9937db12c2', count=100, offset=0)
reply = mc2.submit_application_request(request)
print(reply)


'''
request = mc2.get_stock_entry_list_request('fd3f39fd-01c0-4d02-9f0e-8f9937db12c2', count=100, offset=0)
req2 = mc2.get_vet_document_by_uuid_request('e32c7818-7877-4d8b-afec-58af217c2a4a', 'fd3f39fd-01c0-4d02-9f0e-8f9937db12c2')
reply = mc2.submit_application_request(request)
print(type(reply))
print(reply)
with open('reply.json', 'w', encoding='UTF8') as f:
    f.write(str(mc2.receive_application_result('433b25ab-bbff-4df8-91b0-0b39f0126b20')))

'''