# 🌾 AgroSense - Smart Farming Solutions

> **Complete Agricultural Platform with AI-Powered Crop Intelligence, Marketplace, and Progressive Web App**

[![PWA](https://img.shields.io/badge/PWA-Ready-green)](https://github.com/mohammedsaalim0/agrosense.io)
[![Django](https://img.shields.io/badge/Django-6.0-blue)](https://www.djangoproject.com/)
[![AI](https://img.shields.io/badge/AI-Powered-orange)](https://github.com/mohammedsaalim0/agrosense.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 Features

### 🤖 AI-Powered Agriculture
- **Crop Quality Scanner**: Advanced image analysis for crop quality assessment
- **Market Intelligence**: Real-time price predictions for 40+ crop types
- **Smart Recommendations**: AI-driven farming suggestions
- **Seasonal Trends**: Market data with seasonal price variations

### 🛒 E-Commerce Platform
- **AgroStore**: Complete agricultural marketplace
- **Razorpay Integration**: Secure payment processing
- **Product Catalog**: Seeds, fertilizers, pesticides, tools, and more
- **Order Management**: Complete order tracking and billing

### 📱 Progressive Web App (PWA)
- **Native App Experience**: Install on any device
- **Offline Functionality**: Works without internet connection
- **Home Screen Integration**: Add to device home screen
- **Push Notifications**: Real-time updates and alerts

### 🌍 Market Intelligence
- **40+ Crop Types**: Comprehensive coverage of agricultural products
- **Realistic Pricing**: Based on actual Indian market rates
- **Seasonal Analysis**: Month-by-month price trends
- **Demand/Supply Metrics**: Market insights and predictions

### 🎯 Smart Features
- **User Authentication**: Secure login and registration
- **Dashboard Analytics**: Personalized farming insights
- **Scheme Applications**: Government agricultural schemes
- **Educational Content**: Farming courses and certifications

## 🛠️ Technology Stack

- **Backend**: Django 6.0 + Python 3.14
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (Development), PostgreSQL (Production)
- **AI/ML**: NumPy, PIL, Google Gemini API, Ollama
- **Payments**: Razorpay Integration
- **PWA**: Service Worker, Web App Manifest
- **Deployment**: Whitenoise, Gunicorn

## 📦 Installation

### Prerequisites
- Python 3.14+
- Node.js (for PWA development)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/mohammedsaalim0/agrosense.io.git
cd agrosense.io

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file with the following:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

# Razorpay (Test Mode)
RAZORPAY_KEY_ID=rzp_test_ShKGWsYI9YNXmO
RAZORPAY_KEY_SECRET=DjQ7Y2WwJRt3UAI5tjKA50kU

# Google Gemini API (Optional)
GOOGLE_API_KEY=your-gemini-api-key

# Ollama (Optional for AI features)
OLLAMA_API_URL=http://localhost:11434
```

## 🌐 Usage

### Web Application
1. Navigate to `http://localhost:8000`
2. Register or login to your account
3. Access all features from the dashboard

### PWA Installation
1. Open the application in a supported browser (Chrome, Edge)
2. Click the "Get App" button
3. Follow the browser's install prompt
4. Access AgroSense as a native app

### AI Features
- **Crop Scanner**: Upload crop images for quality analysis
- **Market Intelligence**: Get price predictions for any crop
- **Smart Recommendations**: Receive AI-powered farming advice

## 📱 PWA Features

### Installation
- **Chrome/Edge**: Automatic install prompt
- **Safari**: Manual "Add to Home Screen"
- **Firefox**: PWA install support

### Capabilities
- ✅ Offline access
- ✅ Home screen integration
- ✅ Full-screen mode
- ✅ Push notifications
- ✅ Background sync
- ✅ File handling

## 🤖 AI Integration

### Crop Quality Analysis
- **Image Processing**: Advanced computer vision
- **Quality Scoring**: Scientific accuracy assessment
- **Defect Detection**: Rot, damage, disease identification
- **Price Prediction**: Quality-based pricing

### Market Intelligence
- **40+ Crops**: Comprehensive coverage
- **Seasonal Trends**: Monthly price variations
- **Realistic Data**: Based on actual market rates
- **Smart Analytics**: Demand/supply insights

## 💳 Payment Integration

### Razorpay Setup
1. Create Razorpay account
2. Get test API keys
3. Update environment variables
4. Test payment flow

### Features
- ✅ Secure payment processing
- ✅ Multiple payment methods
- ✅ Order tracking
- ✅ Refund management

## 🎨 UI/UX Features

### Design
- **Modern Interface**: Clean, responsive design
- **Dark Mode**: Toggle between themes
- **Mobile First**: Optimized for all devices
- **Accessibility**: WCAG 2.1 compliant

### Components
- **Dashboard**: Personalized insights
- **Store**: E-commerce marketplace
- **Analytics**: Data visualization
- **Profile**: User management

## 📊 Market Intelligence

### Supported Crops
- **Cereals**: Wheat, Rice, Maize, Jowar, Bajra, Ragi
- **Pulses**: Tur, Moong, Urad, Arhar, Gram, Lentil
- **Oilseeds**: Mustard, Soyabean, Groundnut, Sunflower
- **Vegetables**: Tomato, Potato, Onion, Chilli, Garlic
- **Cash Crops**: Cotton, Sugarcane, Tobacco, Coffee
- **Spices**: Turmeric, Coriander, Cumin, Pepper

### Features
- **Price Predictions**: Real-time market rates
- **Trend Analysis**: Monthly price variations
- **Market Insights**: Demand/supply metrics
- **Seasonal Patterns**: Harvest cycle impacts

## 🔧 Development

### Project Structure
```
agrosense.io/
├── agrosense_project/     # Django settings
├── core/                  # Main application
│   ├── views.py          # API endpoints and views
│   ├── models.py         # Database models
│   ├── templates/        # HTML templates
│   └── urls.py           # URL routing
├── static/               # Static files
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript
│   └── icons/           # PWA icons
├── media/                # User uploads
├── requirements.txt      # Python dependencies
└── README.md           # This file
```

### API Endpoints
- `/api/market-data/` - Market intelligence
- `/api/predict-fair-price/` - Crop quality analysis
- `/api/create-razorpay-order/` - Payment processing
- `/api/verify-razorpay-payment/` - Payment verification

### Testing
```bash
# Run tests
python manage.py test

# Test specific features
python test_crop_prediction.py
python test_market_intelligence.py
python test_razorpay.py
```

## 🚀 Deployment

### Production Setup
1. Set `DJANGO_DEBUG=False`
2. Configure database (PostgreSQL recommended)
3. Set up static files serving
4. Configure domain and HTTPS
5. Set up environment variables

### Docker Deployment
```bash
# Build Docker image
docker build -t agrosense .

# Run container
docker run -p 8000:8000 agrosense
```

### Heroku Deployment
```bash
# Install Heroku CLI
heroku create agrosense-app
git push heroku main
```

## 📈 Performance

### Optimizations
- **Image Processing**: NumPy for faster analysis
- **Caching**: Redis for API responses
- **Database**: Optimized queries
- **Static Files**: CDN integration
- **PWA**: Service worker caching

### Metrics
- **Load Time**: <2 seconds
- **PWA Score**: 95+ Lighthouse
- **Mobile Friendly**: 100% responsive
- **SEO Optimized**: Meta tags and sitemaps

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Django**: Web framework
- **Razorpay**: Payment gateway
- **Google Gemini**: AI API
- **Ollama**: Local AI models
- **NumPy**: Scientific computing
- **Bootstrap**: UI components

## 📞 Contact

- **GitHub**: [@mohammedsaalim0](https://github.com/mohammedsaalim0)
- **Project**: [AgroSense](https://github.com/mohammedsaalim0/agrosense.io)

## 🔗 Links

- **Live Demo**: [Coming Soon]
- **Documentation**: [Wiki](https://github.com/mohammedsaalim0/agrosense.io/wiki)
- **Issues**: [Bug Reports](https://github.com/mohammedsaalim0/agrosense.io/issues)
- **Discussions**: [Community Forum](https://github.com/mohammedsaalim0/agrosense.io/discussions)

---

⭐ **Star this repository if it helped you!**

🌾 **Transforming Agriculture with Technology** 🚀
