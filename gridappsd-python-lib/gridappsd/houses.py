from collections import namedtuple

house_keys = [
    'name',
    'parent',
    'coolingSetpoint',
    'coolingSystem',
    'floorArea',
    'heatingSetpoint',
    'heatingSystem',
    'hvacPowerFactor',
    'numberOfStories',
    'thermalIntegrity',
    'id',
    'fdrid'
]
House = namedtuple('House', house_keys)

# class House(HouseBase):
#     def __dict__


class Houses:
    class __SingltonHouses:
        def __init__(self, gappsd: 'GridAPPSD'):
            self._gappsd = gappsd
            self._houses = {}

        def __str__(self):
            return repr(self) + self._gappsd

        def get_houses_for_feeder(self, feeder):
            if feeder not in self._houses:
                self._populate(feeder)
            return self._houses.get(feeder)

        def _populate(self, feeder):
            query = """# list houses - DistHouse
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/CIM100#>
SELECT ?fdrname ?name ?parent ?coolingSetpoint ?coolingSystem ?floorArea ?heatingSetpoint ?heatingSystem ?hvacPowerFactor ?numberOfStories ?thermalIntegrity ?id ?fdrid 
WHERE { 
#	VALUES ?fdrid {"_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095"}  # R2 12.47 3
#	VALUES ?fdrid {"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"}  # 8500-node
# VALUES ?fdrid {"_E407CBB6-8C8D-9BC9-589C-AB83FBF0826D"}  # 123 PV/Triplex
#   VALUES ?fdrid {"_503D6E20-F499-4CC7-8051-971E23D0BF79"}  # 123 Transactive
   VALUES ?fdrid {"%s"}
   ?h r:type c:House.
   ?h c:IdentifiedObject.name ?name.
   ?h c:IdentifiedObject.mRID ?id.
   ?h c:House.floorArea ?floorArea.
   ?h c:House.numberOfStories ?numberOfStories.
   OPTIONAL{?h c:House.coolingSetpoint ?coolingSetpoint.}
   OPTIONAL{?h c:House.heatingSetpoint ?heatingSetpoint.}
   OPTIONAL{?h c:House.hvacPowerFactor ?hvacPowerFactor.}
   ?h c:House.coolingSystem ?coolingSystemRaw.
   	bind(strafter(str(?coolingSystemRaw),"HouseCooling.") as ?coolingSystem) 
   ?h c:House.heatingSystem ?heatingSystemRaw.
   	bind(strafter(str(?heatingSystemRaw),"HouseHeating.") as ?heatingSystem)
   ?h c:House.thermalIntegrity ?thermalIntegrityRaw.
   	bind(strafter(str(?thermalIntegrityRaw),"HouseThermalIntegrity.") as ?thermalIntegrity)
   ?h c:House.EnergyConsumer ?econ.
   ?econ c:IdentifiedObject.name ?parent.
   ?fdr c:IdentifiedObject.mRID ?fdrid.
   ?fdr c:IdentifiedObject.name ?fdrname.
   ?econ c:Equipment.EquipmentContainer ?fdr.
} ORDER BY ?fdrname ?name
""" % feeder
            response = self._gappsd.query_data(query)
            houses = {}
            for rec in response['data']['results']['bindings']:
                create_order = {}
                name = None
                for d in house_keys:
                    if d == 'name':
                        name = rec[d]['value']
                    try:
                        create_order[d] = rec[d]['value']
                    except KeyError:
                        create_order[d] = None

                houses[name] = House(**create_order)

            self._houses[feeder] = houses


    instance = None

    def __init__(self, gappsd):
        if not Houses.instance:
            Houses.instance = Houses.__SingltonHouses(gappsd)
        else:
            Houses.instance._gappsd = gappsd

    def __getattr__(self, name):
        return getattr(self.instance, name)

