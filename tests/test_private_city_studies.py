"""Private city studies: isolated, versioned, owner-owned GCS object."""
import unittest
from copy import deepcopy
from unittest.mock import Mock

from private_city_studies import (empty_collection,add_study,change_study,
                                  encode_collection,decode_collection,
                                  cloud_load,cloud_commit)
from private_continuity_store import StorageConflict,object_key
from trip_plan_model import new_plan
from city_decision_model import compare_city_decisions
from city_decision_store import make_city_draft
from data_model import load_data


class PrivateCityStudiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=new_plan()
        comparison=compare_city_decisions(cls.plan,["strasbourg"],["luxembourg"],
                                          {},load_data(),False,60,6.3)
        cls.draft=make_city_draft("Mulhouse x Strasbourg",comparison)

    def test_multiple_independent_scenarios_and_roundtrip(self):
        initial=empty_collection()
        first,id1=add_study(initial,self.draft)
        second,id2=add_study(first,self.draft)
        self.assertNotEqual(id1,id2)
        self.assertEqual(initial["studies"],[])
        result=decode_collection(encode_collection(second))
        self.assertEqual(result,second)
        result["studies"][0]["draft"]["notes"]="changed"
        self.assertNotEqual(result,second)

    def test_rename_duplicate_and_delete(self):
        first,ident=add_study(empty_collection(),self.draft)
        updated,same=change_study(first,ident,"rename",name="Nova análise")
        self.assertEqual(same,ident)
        self.assertEqual(updated["studies"][0]["revision"],2)
        self.assertEqual(first["studies"][0]["revision"],1)
        clone,new_id=change_study(updated,ident,"duplicate",name="Outra")
        self.assertNotEqual(ident,new_id)
        self.assertEqual(len(clone["studies"]),2)
        deleted,_=change_study(clone,ident,"delete")
        self.assertEqual(len(deleted["studies"]),1)

    def test_replace_existing_study_preserves_id_and_increments_revision(self):
        initial,ident=add_study(empty_collection(),self.draft)
        revised=deepcopy(self.draft)
        revised["notes"]="Nova pesquisa"
        updated,same=change_study(initial,ident,"replace",draft=revised)
        self.assertEqual(same,ident)
        self.assertEqual(updated["studies"][0]["revision"],2)
        self.assertEqual(updated["studies"][0]["draft"]["notes"],"Nova pesquisa")
        self.assertEqual(initial["studies"][0]["revision"],1)

    def test_study_is_tied_to_reference_plan_id(self):
        collection,ident=add_study(empty_collection(),self.draft,self.plan["plan_id"])
        self.assertEqual(collection["studies"][0]["base_plan_id"],self.plan["plan_id"])
        clone,new_id=change_study(collection,ident,"duplicate")
        self.assertEqual(clone["studies"][-1]["base_plan_id"],self.plan["plan_id"])
        invalid=deepcopy(clone)
        invalid["studies"][0]["base_plan_id"]="../outside"
        with self.assertRaises(ValueError):encode_collection(invalid)

    def test_imported_owner_field_is_never_an_authorization(self):
        collection,ident=add_study(empty_collection(),self.draft)
        collection["studies"][0]["owner"]="someone@example.com"
        with self.assertRaises(ValueError):
            encode_collection(collection)
        self.assertEqual(object_key("owner@example.com"),object_key("OWNER@example.com"))
        self.assertNotEqual(object_key("owner@example.com"),object_key("other@example.com"))

    def test_conflict_does_not_mutate_local_collection(self):
        collection,ident=add_study(empty_collection(),self.draft)
        before=deepcopy(collection)
        store=Mock()
        store.save.side_effect=StorageConflict("changed")
        with self.assertRaises(StorageConflict):
            cloud_commit(store,collection,4)
        store.save.assert_called_once()
        self.assertEqual(store.save.call_args.args[1],4)
        self.assertEqual(collection,before)

    def test_load_absent_and_existing_generation(self):
        store=Mock()
        store.load.return_value=None
        self.assertEqual(cloud_load(store),(empty_collection(),None))
        coll,ident=add_study(empty_collection(),self.draft)
        store.load.return_value=(encode_collection(coll),17)
        self.assertEqual(cloud_load(store),(coll,17))

    def test_triplan_unmodified(self):
        before=deepcopy(self.plan)
        coll,ident=add_study(empty_collection(),self.draft)
        coll,_=change_study(coll,ident,"rename",name="teste")
        self.assertEqual(before,self.plan)

    def test_rejects_oversize_duplicates_and_malformed(self):
        collection,ident=add_study(empty_collection(),self.draft)
        collection["studies"].append(deepcopy(collection["studies"][0]))
        with self.assertRaises(ValueError):encode_collection(collection)
        with self.assertRaises(ValueError):decode_collection(b"bad json")
        with self.assertRaises(ValueError):decode_collection(b"x"*400001)


if __name__=="__main__":
    unittest.main()
