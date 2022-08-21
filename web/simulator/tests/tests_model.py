from cProfile import label
from django.test import TestCase
from ..models import Composite, BaseElement, BaseElementValue, Simulation
import datetime

class ModelTest(TestCase):
    @classmethod
    def setUp(self):
        bat_pack = Composite.objects.create(label="BatPack", description="Cell pack with casing")
        bat_pack.add_root(label="system", description="Set of BatPack")

        start = datetime.datetime.now()
        simulation = Simulation.objects.create(
            title="Simulation Test", 
            description="Une simulation pour tester", 
            start=start, 
            end=start+datetime.timedelta(years=20),
            composition=bat_pack.get_root()
        )

        n_volt_1 = BaseElement.objects.create(
            label="Nominal Voltage", 
            date=datetime.datetime.now,
            quantity=30,
            value="3.2",
            unit="V"
            )
        n_volt_2 = BaseElement.objects.create(
            label="Nominal Voltage", 
            date=(datetime.datetime.now + datetime.timedelta(weeks=10)),
            quantity=30,
            value="3.0",
            unit="V"
            )
        
        bat_pack.add_child(label="Cell", description="Cell of batpack", base_elements=[n_volt_1, n_volt_2])
        bat_pack.add_child(label="Casing", description="Support of cells")

        bat_pack.save()
        simulation.save()
        n_volt_1.save()
        n_volt_2.save()

    def testTotalCost(self):
        simulation = Simulation.objects.get(title="Simulation Test")
        composite_root = Composite.objects.filter(simulation__title="Simulation Test")
        
        total_cost = composite_root.sumByUnit("V")
        self.assertEqual(total_cost, 6.2)
