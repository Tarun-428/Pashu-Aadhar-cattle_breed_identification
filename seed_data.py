#!/usr/bin/env python3
"""
Seed script to populate the cattle breeds database with initial data.
Run this script after setting up the database to add sample breed information.
"""

from app import app, db
from models import CattleBreed

def seed_cattle_breeds():
    """Populate database with cattle breed information"""
    
    breeds_data = [
        {
            'name': 'Holstein_Friesian',
            'scientific_name': 'Bos taurus',
            'origin': 'Netherlands',
            'category': 'Dairy',
            'description': 'Holstein cattle are a breed of dairy cattle originating from the Dutch provinces of North Holland and Friesland. Known for their distinctive black and white markings, they are the most widespread dairy breed in the world.',
            'characteristics': 'Large size, excellent milk production, black and white color pattern, docile temperament, high feed conversion efficiency.',
            'average_weight_male': 900,
            'average_weight_female': 580,
            'average_height': 145,
            'average_length':242,
            'average_width':64,
            'milk_production': 22,
            'color_pattern': 'Black and white patches',
            'temperament': 'Docile',
            'climate_adaptation': 'Temperate',
            'image_url': 'https://cdn.britannica.com/53/157153-050-E5582B5A/Holstein-cow.jpg'
        },
        {
            'name': 'Jersey',
            'scientific_name': 'Bos taurus',
            'origin': 'Jersey, Channel Islands',
            'category': 'Dairy',
            'description': 'A small to medium-sized breed of dairy cattle known for its high-quality milk, which has a high butterfat content. They are adaptable to a wide range of climates and conditions.',
            'characteristics': 'Fawn-colored coat, large eyes, dished forehead, black nose and tail switch, high butterfat milk, heat tolerant.',
            'average_weight_male': 700,
            'average_weight_female': 450,
            'average_height': 125,
            'average_length':139,
            'average_width':28,
            'milk_production': 18,
            'color_pattern': 'Light brown to dark fawn',
            'temperament': 'Docile and curious',
            'climate_adaptation': 'Highly adaptable',
            'image_url': 'https://media.istockphoto.com/id/1615976000/photo/indian-cow-standing-in-the-agriculture-field.jpg?s=612x612&w=0&k=20&c=fMKcxdF9v_RH7JxUhsFAryU-4w5ivCb9FbHhRvWbJhw='
        },
        {
            'name': 'Gir',
            'scientific_name': 'Bos indicus',
            'origin': 'Gujarat, India',
            'category': 'Dairy',
            'description': 'The Gir is one of the principal Zebu breeds in India, used for both dairy and beef production. It is known for its distinctive appearance, with a rounded and domed forehead and long, pendulous ears.',
            'characteristics': 'Convex forehead, long pendulous ears, heat and disease resistant, good for tropical climates.',
            'average_weight_male': 600,
            'average_weight_female': 425,
            'average_height': 132,
            'average_length':131,
            'average_width':23,
            'milk_production': 8,
            'color_pattern': 'Spotted red and white',
            'temperament': 'Docile and gentle',
            'climate_adaptation': 'Tropical',
            'image_url': 'https://images.pexels.com/photos/33778098/pexels-photo-33778098.jpeg?_gl=1*sgolqm*_ga*OTI1MzA2MTExLjE3NDc4OTc4ODc.*_ga_8JE65Q40S6*czE3NTc0NDAwODYkbzE5JGcxJHQxNzU3NDQwNjY3JGoyNiRsMCRoMA..'
        },
        {
            'name': 'Sahiwal',
            'scientific_name': 'Bos indicus',
            'origin': 'Punjab, Pakistan/India',
            'category': 'Dairy',
            'description': 'The Sahiwal is a breed of zebu cattle, primarily used in dairy production. It is considered one of the best dairy breeds of the Indian subcontinent due to its high milk yield and resistance to heat and ticks.',
            'characteristics': 'Reddish-brown color, loose skin, tick-resistant, heat-tolerant, high milk production.',
            'average_weight_male': 450,
            'average_weight_female': 750,
            'average_height': 135,
            'average_length':131,
            'average_width':25,
            'milk_production': 9,
            'color_pattern': 'Reddish-brown to greyish-red',
            'temperament': 'Docile',
            'climate_adaptation': 'Tropical',
            'image_url': 'https://i.pinimg.com/736x/4f/68/5c/4f685cdd699b9cc078320eb9ac8e3228.jpg'
        },
        {
            'name': 'Murrah',
            'scientific_name': 'Bubalus bubalis',
            'origin': 'Haryana, India',
            'category': 'Dairy (Buffalo)',
            'description': 'The Murrah buffalo is a breed of water buffalo mainly kept for milk production. It is one of the most productive dairy buffalo breeds in the world.',
            'characteristics': 'Jet-black color, tightly curled horns, massive body, high milk yield with high butterfat content.',
            'average_weight_male': 675,
            'average_weight_female': 575,
            'average_height': 137,
            'average_length':148,
            'average_width':49,
            'milk_production': 8,
            'color_pattern': 'Jet-black',
            'temperament': 'Generally docile',
            'climate_adaptation': 'Tropical',
            'image_url': 'https://images.pexels.com/photos/321527/pexels-photo-321527.jpeg?_gl=1*109ggcf*_ga*OTI1MzA2MTExLjE3NDc4OTc4ODc.*_ga_8JE65Q40S6*czE3NTc0NDAwODYkbzE5JGcxJHQxNzU3NDQwMTYwJGo2MCRsMCRoMA..'
        },
        {
            'name': 'Jaffarabadi',
            'scientific_name': 'Bubalus bubalis',
            'origin': 'Gujarat, India',
            'category': 'Dairy (Buffalo)',
            'description': 'Jaffarabadi buffaloes are a riverine breed of buffalo from Gujarat, India. They are known for their massive build and are one of the heaviest buffalo breeds.',
            'characteristics': 'Massive, heavy body; drooping horns that curve upwards at the tip; prominent forehead.',
            'average_weight_male': 1300,
            'average_weight_female': 1050,
            'average_height': 145,
            'average_length':163,
            'average_width':68,
            'milk_production': 7.5,
            'color_pattern': 'Black',
            'temperament': 'Generally docile',
            'climate_adaptation': 'Tropical',
            'image_url': 'https://i.pinimg.com/1200x/98/a3/a0/98a3a08d22b33085fab27bd32224d31c.jpg'
        }
    ]
    
    # Clear existing data
    print("Clearing existing breed data...")
    CattleBreed.query.delete()
    
    # Add new breed data
    print("Adding cattle breed data...")
    for breed_data in breeds_data:
        breed = CattleBreed(**breed_data)
        db.session.add(breed)
        print(f"Added: {breed_data['name']}")
    
    # Commit changes
    db.session.commit()
    print(f"\nSuccessfully added {len(breeds_data)} cattle breeds to the database!")

if __name__ == '__main__':
    with app.app_context():
        print("Starting database seeding...")
        seed_cattle_breeds()
        print("Database seeding completed!")
