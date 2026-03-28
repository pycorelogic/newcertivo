#!/usr/bin/env python3
"""
Certivo Blog - Application Entry Point

This script starts the Flask development server.
For production deployment, use a WSGI server like Gunicorn.
"""

import os
import sys

from app import create_app

# Create the Flask application instance
app = create_app()


def init_database():
    """Initialize the database with tables and seed data if needed."""
    from app.extensions import db
    from app.models.category import Category
    from app.models.post import Post
    from app.models.user import User

    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if we need to seed initial data
        if User.query.count() == 0:
            print("🌱 Seeding initial data...")
            seed_initial_data()
            print("✅ Initial data seeded successfully!")


def seed_initial_data():
    """Seed the database with initial data."""
    from datetime import datetime, timedelta

    from slugify import slugify
    from werkzeug.security import generate_password_hash

    from app.extensions import db
    from app.models.category import Category
    from app.models.contact import AffiliateLink
    from app.models.post import Post
    from app.models.user import User

    # Create admin user
    admin = User(
        username="admin",
        email="admin@certivo.com",
        password_hash=generate_password_hash(os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!Secure")),
        is_admin=True,
    )
    db.session.add(admin)
    db.session.flush()  # Get the admin ID

    # Create categories
    categories_data = [
        {
            "name": "Technology",
            "description": "Latest tech news, reviews, and tutorials",
        },
        {
            "name": "Business",
            "description": "Business insights, strategies, and success stories",
        },
        {"name": "Lifestyle", "description": "Health, wellness, and lifestyle tips"},
        {
            "name": "Travel",
            "description": "Travel guides, tips, and destination reviews",
        },
        {
            "name": "Food",
            "description": "Recipes, restaurant reviews, and culinary adventures",
        },
        {
            "name": "Finance",
            "description": "Personal finance, investing, and money management",
        },
    ]

    categories = []
    for cat_data in categories_data:
        category = Category(
            name=cat_data["name"],
            slug=slugify(cat_data["name"]),
            description=cat_data["description"],
        )
        db.session.add(category)
        categories.append(category)

    db.session.flush()

    # Create sample blog posts
    posts_data = [
        {
            "title": "Getting Started with Python Flask: A Beginner's Guide",
            "content": """
                <p>Flask is a lightweight and powerful web framework for Python that makes it easy to build web applications.
                In this comprehensive guide, we'll walk you through everything you need to know to get started with Flask.</p>

                <h2>Why Choose Flask?</h2>
                <p>Flask is often called a "micro" framework because it keeps the core simple but extensible.
                This makes it perfect for both small projects and large applications.</p>

                <h3>Key Features:</h3>
                <ul>
                    <li>Built-in development server and debugger</li>
                    <li>RESTful request dispatching</li>
                    <li>Jinja2 templating engine</li>
                    <li>Support for secure cookies</li>
                    <li>Extensive documentation</li>
                </ul>

                <h2>Installation</h2>
                <p>Installing Flask is straightforward with pip:</p>
                <pre><code>pip install flask</code></pre>

                <h2>Your First Flask App</h2>
                <p>Here's a simple "Hello World" example:</p>
                <pre><code>from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)</code></pre>

                <p>Flask makes web development in Python accessible and enjoyable. Start building today!</p>
            """,
            "excerpt": "Learn how to build web applications with Flask, Python's lightweight and powerful web framework. Perfect for beginners and experienced developers alike.",
            "category": 0,
            "is_featured": True,
        },
        {
            "title": "10 Essential Business Strategies for 2024",
            "content": """
                <p>As we navigate through 2024, businesses need to adapt to changing market conditions and consumer behaviors.
                Here are ten essential strategies that every business should consider implementing this year.</p>

                <h2>1. Digital Transformation</h2>
                <p>Embrace digital tools and platforms to streamline operations and enhance customer experience.
                Cloud computing, AI, and automation are no longer optional—they're essential.</p>

                <h2>2. Customer-Centric Approach</h2>
                <p>Put your customers at the heart of everything you do. Gather feedback, personalize experiences,
                and build lasting relationships.</p>

                <h2>3. Sustainable Practices</h2>
                <p>Consumers increasingly value sustainability. Implement eco-friendly practices and communicate
                your commitment to environmental responsibility.</p>

                <h2>4. Remote Work Optimization</h2>
                <p>Hybrid and remote work models are here to stay. Invest in collaboration tools and create
                policies that support flexible work arrangements.</p>

                <h2>5. Data-Driven Decision Making</h2>
                <p>Leverage analytics to make informed decisions. Understanding your data gives you a competitive edge.</p>

                <blockquote>
                    <p>"The goal is to turn data into information, and information into insight."</p>
                    <cite>Carly Fiorina, Former CEO of HP</cite>
                </blockquote>

                <p>By implementing these strategies, your business will be well-positioned for success in 2024 and beyond.</p>
            """,
            "excerpt": "Discover the top business strategies that will help your company thrive in 2024. From digital transformation to sustainability, learn what matters most.",
            "category": 1,
            "is_featured": True,
        },
        {
            "title": "The Ultimate Guide to Healthy Living in a Busy World",
            "content": """
                <p>Maintaining a healthy lifestyle while juggling work, family, and personal commitments can be challenging.
                This guide provides practical tips to help you prioritize your health without overwhelming your schedule.</p>

                <h2>Start Your Day Right</h2>
                <p>Morning routines set the tone for your entire day. Wake up at a consistent time, hydrate immediately,
                and consider incorporating light exercise or meditation.</p>

                <h2>Nutrition Made Simple</h2>
                <ul>
                    <li><strong>Meal Prep:</strong> Dedicate a few hours on weekends to prepare healthy meals</li>
                    <li><strong>Balanced Plates:</strong> Fill half your plate with vegetables, a quarter with protein, and a quarter with whole grains</li>
                    <li><strong>Healthy Snacks:</strong> Keep nuts, fruits, and vegetables readily available</li>
                    <li><strong>Hydration:</strong> Aim for 8 glasses of water daily</li>
                </ul>

                <h2>Movement Matters</h2>
                <p>You don't need hours at the gym. Even 20-30 minutes of daily activity makes a significant difference.
                Find activities you enjoy—walking, dancing, yoga, or swimming.</p>

                <h2>Mental Health is Essential</h2>
                <p>Don't neglect your mental wellbeing. Practice mindfulness, maintain social connections,
                and don't hesitate to seek professional help when needed.</p>

                <p>Remember, healthy living is a journey, not a destination. Small, consistent changes lead to lasting results.</p>
            """,
            "excerpt": "Learn how to maintain a healthy lifestyle even with a packed schedule. Practical tips for nutrition, exercise, and mental wellbeing.",
            "category": 2,
            "is_featured": True,
        },
        {
            "title": "Hidden Gems: 15 Underrated Travel Destinations for 2024",
            "content": """
                <p>Tired of overcrowded tourist hotspots? Discover these incredible destinations that offer authentic
                experiences without the massive crowds.</p>

                <h2>1. Porto, Portugal</h2>
                <p>While Lisbon gets all the attention, Porto offers stunning architecture, delicious port wine,
                and a more relaxed atmosphere along the Douro River.</p>

                <h2>2. Tbilisi, Georgia</h2>
                <p>This former Soviet republic offers incredible cuisine, ancient history, and some of the warmest
                hospitality you'll find anywhere.</p>

                <h2>3. Oaxaca, Mexico</h2>
                <p>A cultural treasure with indigenous traditions, world-class cuisine, and nearby archaeological sites
                like Monte Albán.</p>

                <h2>4. Luang Prabang, Laos</h2>
                <p>A UNESCO World Heritage site where French colonial architecture meets Buddhist temples and
                stunning natural beauty.</p>

                <h2>5. Slovenia</h2>
                <p>From Lake Bled to Ljubljana, Slovenia offers Alpine scenery, medieval castles, and excellent wine
                regions—all in a compact, accessible country.</p>

                <h3>Travel Tips</h3>
                <ul>
                    <li>Visit during shoulder season for better prices and fewer crowds</li>
                    <li>Learn basic phrases in the local language</li>
                    <li>Support local businesses and avoid chain restaurants</li>
                    <li>Be respectful of local customs and traditions</li>
                </ul>

                <p>These destinations offer authentic cultural experiences at a fraction of the cost of more popular locations.</p>
            """,
            "excerpt": "Explore 15 amazing travel destinations that most tourists haven't discovered yet. Authentic experiences, lower prices, and fewer crowds await.",
            "category": 3,
            "is_featured": False,
        },
        {
            "title": "Master the Art of Sourdough: A Complete Guide",
            "content": """
                <p>Sourdough bread has experienced a renaissance in recent years, and for good reason. The tangy flavor,
                chewy texture, and health benefits make it worth the effort to master at home.</p>

                <h2>Creating Your Starter</h2>
                <p>Your sourdough journey begins with creating a starter—a living culture of wild yeast and bacteria.
                Mix equal parts flour and water, and feed it daily for about a week until it's bubbly and active.</p>

                <h2>The Basic Sourdough Recipe</h2>
                <p><strong>Ingredients:</strong></p>
                <ul>
                    <li>500g bread flour</li>
                    <li>350g water</li>
                    <li>100g active starter</li>
                    <li>10g salt</li>
                </ul>

                <h2>The Process</h2>
                <p><strong>1. Autolyse:</strong> Mix flour and water, rest for 30 minutes<br>
                <strong>2. Mix:</strong> Add starter and salt, develop gluten<br>
                <strong>3. Bulk Fermentation:</strong> 4-6 hours with periodic folding<br>
                <strong>4. Shape:</strong> Form into a tight boule<br>
                <strong>5. Cold Proof:</strong> Refrigerate overnight<br>
                <strong>6. Bake:</strong> 450°F in a Dutch oven</p>

                <h2>Troubleshooting Common Issues</h2>
                <p><strong>Dense bread:</strong> Under-fermented or weak starter<br>
                <strong>Too sour:</strong> Over-fermented<br>
                <strong>Flat bread:</strong> Over-proofed or insufficient gluten development</p>

                <blockquote>
                    <p>"Bread baking is one of those almost hypnotic businesses, like a dance from some ancient ceremony."</p>
                    <cite>M.F.K. Fisher</cite>
                </blockquote>

                <p>With practice and patience, you'll be baking bakery-quality sourdough at home!</p>
            """,
            "excerpt": "Learn how to bake delicious, artisan sourdough bread at home. From creating your starter to baking the perfect loaf, we cover everything.",
            "category": 4,
            "is_featured": False,
        },
        {
            "title": "Cryptocurrency 101: A Beginner's Guide to Digital Assets",
            "content": """
                <p>Cryptocurrency has moved from the fringes to mainstream finance. Whether you're curious about Bitcoin,
                exploring NFTs, or considering investing, this guide will help you understand the basics.</p>

                <h2>What is Cryptocurrency?</h2>
                <p>Cryptocurrency is digital or virtual currency that uses cryptography for security. Unlike traditional
                currencies, most cryptocurrencies operate on decentralized networks based on blockchain technology.</p>

                <h2>Popular Cryptocurrencies</h2>
                <ul>
                    <li><strong>Bitcoin (BTC):</strong> The original and most valuable cryptocurrency</li>
                    <li><strong>Ethereum (ETH):</strong> Platform for smart contracts and decentralized applications</li>
                    <li><strong>Cardano (ADA):</strong> Focus on sustainability and peer-reviewed development</li>
                    <li><strong>Solana (SOL):</strong> High-speed blockchain for DeFi and NFTs</li>
                </ul>

                <h2>How to Get Started</h2>
                <p><strong>1. Educate Yourself:</strong> Understand the technology and risks<br>
                <strong>2. Choose an Exchange:</strong> Coinbase, Binance, or Kraken are popular options<br>
                <strong>3. Secure Your Assets:</strong> Use hardware wallets for long-term storage<br>
                <strong>4. Start Small:</strong> Only invest what you can afford to lose<br>
                <strong>5. Diversify:</strong> Don't put all your eggs in one basket</p>

                <h2>Important Considerations</h2>
                <p><strong>Volatility:</strong> Crypto prices can swing dramatically<br>
                <strong>Security:</strong> You're responsible for protecting your assets<br>
                <strong>Regulations:</strong> Laws vary by country and are evolving<br>
                <strong>Taxes:</strong> Crypto transactions may be taxable events</p>

                <p>Cryptocurrency represents an exciting frontier in finance, but it's essential to approach it with
                knowledge and caution.</p>
            """,
            "excerpt": "New to cryptocurrency? This beginner-friendly guide explains what crypto is, how it works, and how to get started safely.",
            "category": 5,
            "is_featured": False,
        },
    ]

    for i, post_data in enumerate(posts_data):
        post = Post(
            title=post_data["title"],
            slug=slugify(post_data["title"]),
            content=post_data["content"],
            excerpt=post_data["excerpt"],
            author_id=admin.id,
            category_id=categories[post_data["category"]].id,
            is_published=True,
            is_featured=post_data["is_featured"],
            published_at=datetime.utcnow() - timedelta(days=len(posts_data) - i),
            views=(i + 1) * 50,  # Fake some view counts
        )
        db.session.add(post)

    # Create sample affiliate links
    affiliates_data = [
        {
            "title": "Best Web Hosting",
            "description": "Get 50% off premium hosting plans",
            "url": "https://example.com/hosting",
            "cta_text": "Get Discount",
            "is_sidebar": True,
            "position": 1,
        },
        {
            "title": "Learn to Code",
            "description": "Premium coding courses at a discounted rate",
            "url": "https://example.com/courses",
            "cta_text": "Start Learning",
            "is_sidebar": True,
            "position": 2,
        },
        {
            "title": "Travel Insurance",
            "description": "Protect your trips with comprehensive coverage",
            "url": "https://example.com/insurance",
            "cta_text": "Get Quote",
            "is_sidebar": True,
            "position": 3,
        },
    ]

    for aff_data in affiliates_data:
        affiliate = AffiliateLink(**aff_data)
        db.session.add(affiliate)

    # Commit all changes
    db.session.commit()


if __name__ == "__main__":
    # Check if we should initialize the database
    if "--init-db" in sys.argv:
        init_database()
        sys.exit(0)

    # Get configuration from environment
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 8000))

    print("=" * 60)
    print(f"🚀 Starting Certivo Blog")
    print(f"📍 Running on: http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"🗄️  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 60)
    print("\n💡 Tip: Run with --init-db to seed sample data")
    
    # Security warning for production
    if os.environ.get("FLASK_ENV") == "production":
        print("\n⚠️  PRODUCTION MODE: Ensure you've changed the default admin password!")
        print("⚠️  Set DEFAULT_ADMIN_PASSWORD environment variable\n")
    else:
        print("🔐 Default admin: admin@certivo.com / ChangeMe123!Secure\n")

    # Run the application
    app.run(debug=debug, host=host, port=port, use_reloader=debug)
