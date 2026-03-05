"""
World Locations Data for YouTube Video Topics.
Contains countries, states, and cities from around the world.
"""

LOCATIONS = {
    "countries": [
        # Asia
        "Japan", "China", "India", "Thailand", "Vietnam", "Indonesia", "Malaysia",
        "Singapore", "South Korea", "Philippines", "Nepal", "Sri Lanka", "Bangladesh",
        "Pakistan", "UAE", "Saudi Arabia", "Israel", "Turkey", "Iran",
        
        # Europe
        "France", "Germany", "Italy", "Spain", "United Kingdom", "Netherlands",
        "Switzerland", "Austria", "Greece", "Portugal", "Sweden", "Norway",
        "Denmark", "Finland", "Belgium", "Poland", "Czech Republic", "Ireland",
        "Scotland", "Croatia", "Hungary", "Romania", "Ukraine", "Russia",
        
        # Americas
        "USA", "Canada", "Mexico", "Brazil", "Argentina", "Chile", "Peru",
        "Colombia", "Cuba", "Jamaica", "Costa Rica", "Panama", "Ecuador",
        
        # Africa
        "Egypt", "Morocco", "South Africa", "Kenya", "Tanzania", "Nigeria",
        "Ghana", "Ethiopia", "Tunisia", "Zimbabwe", "Botswana", "Namibia",
        
        # Oceania
        "Australia", "New Zealand", "Fiji", "Bali", "Hawaii",
    ],
    
    "cities": [
        # Asia
        "Tokyo", "Kyoto", "Osaka", "Beijing", "Shanghai", "Hong Kong", "Mumbai",
        "Delhi", "Jaipur", "Varanasi", "Goa", "Kerala", "Bangkok", "Phuket",
        "Hanoi", "Ho Chi Minh City", "Singapore", "Kuala Lumpur", "Seoul",
        "Busan", "Manila", "Kathmandu", "Dubai", "Abu Dhabi", "Jerusalem",
        "Istanbul", "Bali", "Jakarta",
        
        # Europe
        "Paris", "London", "Rome", "Venice", "Florence", "Milan", "Barcelona",
        "Madrid", "Amsterdam", "Berlin", "Munich", "Vienna", "Prague", "Budapest",
        "Athens", "Santorini", "Lisbon", "Porto", "Stockholm", "Copenhagen",
        "Oslo", "Helsinki", "Brussels", "Zurich", "Geneva", "Dublin", "Edinburgh",
        "Monaco", "Nice", "Dubrovnik", "Split", "Krakow", "Warsaw", "Moscow",
        "St Petersburg",
        
        # Americas
        "New York", "Los Angeles", "San Francisco", "Las Vegas", "Miami",
        "Chicago", "Boston", "Seattle", "Washington DC", "New Orleans",
        "Toronto", "Vancouver", "Montreal", "Mexico City", "Cancun",
        "Rio de Janeiro", "Sao Paulo", "Buenos Aires", "Lima", "Bogota",
        "Havana", "Cartagena", "Cusco", "Machu Picchu",
        
        # Africa & Middle East
        "Cairo", "Marrakech", "Cape Town", "Johannesburg", "Nairobi",
        "Zanzibar", "Casablanca", "Luxor", "Petra",
        
        # Oceania
        "Sydney", "Melbourne", "Auckland", "Queenstown", "Gold Coast",
    ],
    
    "states_regions": [
        # India
        "Rajasthan", "Kerala", "Goa", "Kashmir", "Himachal Pradesh", "Punjab",
        "Gujarat", "Maharashtra", "Tamil Nadu", "Karnataka", "Uttarakhand",
        
        # USA
        "California", "Texas", "Florida", "New York State", "Hawaii", "Alaska",
        "Arizona", "Colorado", "Nevada", "Oregon", "Washington State",
        
        # Other
        "Bavaria Germany", "Tuscany Italy", "Provence France", "Andalusia Spain",
        "Scottish Highlands", "Swiss Alps", "Canadian Rockies", "Patagonia",
        "Queensland Australia", "South Island New Zealand", "Hokkaido Japan",
    ],
    
    "landmarks": [
        "Eiffel Tower Paris", "Colosseum Rome", "Great Wall of China",
        "Taj Mahal India", "Machu Picchu Peru", "Pyramids of Giza Egypt",
        "Statue of Liberty New York", "Big Ben London", "Sydney Opera House",
        "Christ the Redeemer Brazil", "Angkor Wat Cambodia", "Petra Jordan",
        "Santorini Greece", "Northern Lights Iceland", "Grand Canyon USA",
        "Niagara Falls", "Victoria Falls", "Mount Fuji Japan", "Maldives",
        "Bora Bora", "Swiss Alps", "Amazon Rainforest", "Great Barrier Reef",
        "Serengeti Tanzania", "Galapagos Islands", "Stonehenge England",
    ]
}

# Topic templates for variety
TOPIC_TEMPLATES = [
    "Amazing Facts About {location}",
    "Top 10 Things to Know About {location}",
    "{location} - Hidden Secrets Revealed",
    "Why {location} is So Famous",
    "Incredible {location} Facts You Never Knew",
    "{location} - Must Know Facts",
    "Mind Blowing Facts About {location}",
    "The Truth About {location}",
    "{location} - What They Don't Tell You",
    "Secrets of {location}",
    "{location} Facts That Will Shock You",
    "Amazing {location} - Facts and History",
]


def get_random_topic():
    """Get a random location-based topic."""
    import random
    
    # Choose category
    category = random.choice(list(LOCATIONS.keys()))
    location = random.choice(LOCATIONS[category])
    template = random.choice(TOPIC_TEMPLATES)
    
    return template.format(location=location)


def get_all_topics():
    """Generate all possible topics."""
    topics = []
    for category in LOCATIONS.values():
        for location in category:
            for template in TOPIC_TEMPLATES:
                topics.append(template.format(location=location))
    return topics


if __name__ == "__main__":
    # Test
    for _ in range(10):
        print(get_random_topic())
