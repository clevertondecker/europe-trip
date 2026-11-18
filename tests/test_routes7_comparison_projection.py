import copy
import unittest

from routes7_comparison_projection import decorate_comparison
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import empty_interests, set_interest
from ux503_destination_base_comparison_model import compare_wishlist_bases

class Route7UXTests(unittest.TestCase):
    def test_same_wishes_three_bases_and_non_destructive_labels(self):
        d=build_destination_discovery()
        wishes=empty_interests()
        for place in ("belfort","haguenau","mulhouse","brussels","ghent"):
            wishes=set_interest(wishes,place,"interested",d)
        before=copy.deepcopy(wishes)
        comparison=compare_wishlist_bases(wishes,["mulhouse","strasbourg","lille"],discovery=d)
        orig=copy.deepcopy(comparison)
        view=decorate_comparison(comparison)
        self.assertEqual(view["total"],15)
        self.assertEqual(view["reference_only"],9)
        self.assertEqual(view["local"],1)
        self.assertEqual(view["no_time"],0)
        self.assertIn("mínimo publicado",view["cells"][("mulhouse","belfort")]["label"])
        self.assertIn("ida histórica",view["cells"][("lille","ghent")]["label"])
        self.assertEqual(comparison,orig)
        self.assertEqual(wishes,before)
        self.assertFalse(view["comparison_mutated"])

    def test_averages_not_implied_when_unknown(self):
        d=build_destination_discovery()
        wishes=empty_interests()
        wishes=set_interest(wishes,"belfort","interested",d)
        comp=compare_wishlist_bases(wishes,["mulhouse","strasbourg"],discovery=d)
        view=decorate_comparison(comp)
        self.assertEqual(view["cells"][("mulhouse","belfort")]["typical_label"],
                         "Tempo típico não pesquisado")
        self.assertIn("média publicada",view["cells"][("strasbourg","belfort")]["typical_label"])

if __name__=="__main__":
    unittest.main()
