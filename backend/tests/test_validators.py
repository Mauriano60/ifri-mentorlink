import sys
sys.path.insert(0, 'D:\\Projet_integrateur\\PIL1_2526_61\\backend')
from utils.validators import valider_email, valider_telephone, valider_mot_de_passe, valider_competences_et_lacunes

class TestValidateurs:
    def test_email_valide(self):
        assert valider_email("test@example.com")
        assert valider_email("prenom.nom@universite.bj")

    def test_email_invalide(self):
        assert not valider_email("pas-un-email")
        assert not valider_email("")
        assert not valider_email("@.")

    def test_telephone_benin(self):
        assert valider_telephone("+229 01 23 45 67 89")
        assert valider_telephone("+2290123456789")

    def test_telephone_invalide(self):
        assert not valider_telephone("+225 01 23 45 67")
        assert not valider_telephone("abc")

    def test_mot_de_passe_valide(self):
        valide, msg = valider_mot_de_passe("Test1234")
        assert valide
        assert msg is None

    def test_mot_de_passe_trop_court(self):
        valide, msg = valider_mot_de_passe("Ab1")
        assert not valide
        assert "8" in msg

    def test_mot_de_passe_sans_majuscule(self):
        valide, msg = valider_mot_de_passe("test1234")
        assert not valide
        assert "majuscule" in msg

    def test_competences_max_4(self):
        valide, msg = valider_competences_et_lacunes([1, 2, 3, 4, 5], [])
        assert not valide
        assert "4" in msg

    def test_lacunes_max_4(self):
        valide, msg = valider_competences_et_lacunes([], [1, 2, 3, 4, 5])
        assert not valide
        assert "4" in msg

    def test_pas_de_doublon(self):
        valide, msg = valider_competences_et_lacunes([1, 2], [2, 3])
        assert not valide
        assert "simultanément" in msg

    def test_competences_valides(self):
        valide, msg = valider_competences_et_lacunes([1, 2], [3, 4])
        assert valide
        assert msg is None
