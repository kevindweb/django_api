import json
from datetime import datetime
from django.core.management import BaseCommand
from dog_info.models import Dog

date_format = "%m/%d/%Y"

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('./dog_data.json') as file:
            data = json.load(file)
            if(data and len(data["dog_list"]) > 0):
                dog_list = data["dog_list"]
                for dog_item in dog_list:
                    # loop through each peice of data
                    dog = Dog()
                    dog.name = dog_item["name"] if dog_item["name"] else ""
                    birth_day = dog_item["birth_day"] if dog_item["birth_day"] else "08/26/1998"
                    dog.birth_day = datetime.strptime(birth_day, date_format)
                    dog.breed = dog_item["breed"] if dog_item["breed"] else ""
                    dog.favorite_activity = dog_item["favorite_activity"] if dog_item["favorite_activity"] else ""
                    dog.sex = dog_item["sex"] if dog_item["sex"] else ""
                    # save to database
                    dog.save()
            else:
                print("Could not load the json data")