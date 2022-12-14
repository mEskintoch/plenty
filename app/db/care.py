import json
import datetime as dt
import logging
from typing import Union

from app.db.base import PlentyBaseAppModel
from app.db import PlentyDatabase
from app.db.utils import norm_species

logger = logging.getLogger('app.care.care')


class CareHistory(PlentyBaseAppModel):
    _schema = [
        "id text, cond text, date text"
    ]

    def __init__(self, plantae_id: str):
        self.plantae_id = plantae_id
        self.hist = self.get(self.plantae_id)
        self.today = dt.date.today()

    @staticmethod
    def query(plantae_id):
        with PlentyDatabase() as db:
            q = db.cursor.execute(
                "SELECT * FROM care_history WHERE id = :plant_id",
                {'plant_id': plantae_id}
            )
            res = q.fetchall()
        return res

    @classmethod
    def get(cls, plantae_id):
        if q := cls.query(plantae_id):
            return q
        else:
            logger.debug(
                """
                no history found for plant: {plantae_id}
                """.format(plantae_id=plantae_id)
            )
            return []

    def add(self, date: Union[str, dt.date], cond: str):
        with PlentyDatabase() as db:
            db.insert(table='care_history', values=(self.plantae_id, cond, date))

    def __call__(self, key):
        return [
            dt.datetime.strptime(row[2], "%Y-%m-%d").date()
            for row in self.hist
            if row[1] == key
        ]


class CareNeeds(PlentyBaseAppModel):
    _schema = [
        'species text, opt_cond_map text'
    ]
    data = dict()

    @staticmethod
    def query(species):
        with PlentyDatabase() as db:
            q = db.cursor.execute(
                "SELECT * FROM care_needs WHERE species = :species",
                {'species': norm_species(species)}
            )
            res = q.fetchone()
        return res

    @classmethod
    def get(cls, species: str):
        species = norm_species(species)
        if not cls.data.get(species):
            needs = cls.query(species)
            res = json.loads(needs[1])
            cls.data[species] = res
            return res
        else:
            logger.debug('data is already loaded.')
            return cls.data.get(species, {})

    @staticmethod
    def add(species: str, needs: dict):
        with PlentyDatabase() as db:
            db.insert(table='care_needs', values=(norm_species(species), json.dumps(needs)))

    @staticmethod
    def update_needs(species: str, needs: dict):
        with PlentyDatabase() as db:
            db.cursor.execute(
                "UPDATE care_needs SET opt_cond_map = :needs WHERE species = :species",
                {"species": norm_species(species), 'needs': json.dumps(needs)}
            )
