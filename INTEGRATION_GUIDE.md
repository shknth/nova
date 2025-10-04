# 🚀 API Integration Guide

## Overview
The frontend is **extremely easy** to integrate with APIs! Here's how clean it is:

## 🎯 Super Simple Integration

### Before (Messy):
```javascript
// Scattered mock data everywhere
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  // Mock data generation mixed with component logic
  setData({ aqi: 42, temperature: 22 });
  setLoading(false);
}, []);
```

### After (Clean):
```javascript
// One line API integration!
const { data, loading, error } = useCurrentAirQuality(location);
```

## 📁 Clean Architecture

```
frontend/src/
├── services/
│   ├── apiService.js      # 🔌 Raw API calls
│   └── dataService.js     # 🎯 Smart data layer (mock/real)
├── hooks/
│   └── useApi.js          # 🪝 Reusable data hooks
├── config/
│   └── environment.js     # ⚙️ Environment settings
└── components/            # 🎨 UI components (clean!)
```

## 🔄 Integration Steps

### Step 1: Switch to Real APIs
```javascript
// In .env or environment.js
REACT_APP_USE_MOCK_DATA=false  // Switch to real APIs
REACT_APP_API_URL=https://your-api.com/api
```

### Step 2: Update Backend Endpoints
The frontend expects these endpoints (already defined in `apiService.js`):

```javascript
// AI Chat
POST /api/chat/query
{ "query": "Is it safe to jog today?" }

// Air Quality
GET /api/air-quality/current?location=dublin
GET /api/air-quality/forecast?location=dublin&days=7
POST /api/air-quality/query-analysis
{ "query": "asthma dublin park" }

// Regional Data
GET /api/air-quality/regional?bounds=...

// Health Impact
POST /api/health/impact
{ "location": "dublin", "conditions": ["asthma"] }

// Model Predictions
POST /api/model/predict
{ "features": [[...]] }
```

### Step 3: Component Integration Examples

#### ✅ Current Air Quality (1 line!)
```javascript
const { data, loading, error } = useCurrentAirQuality('dublin');
```

#### ✅ Query-Specific Data
```javascript
const { data, loading, error } = useQueryData(userQuery);
```

#### ✅ AI Chat Submission
```javascript
const { submitQuery, loading, response } = useQuerySubmission();
const handleSubmit = async (query) => {
  const aiResponse = await submitQuery(query);
  // Handle response
};
```

## 🎛️ Configuration Options

### Development Mode (Mock Data)
```javascript
// Uses mock data, perfect for development
REACT_APP_USE_MOCK_DATA=true
```

### Production Mode (Real APIs)
```javascript
// Uses real backend APIs
REACT_APP_USE_MOCK_DATA=false
REACT_APP_API_URL=https://your-production-api.com/api
```

## 🔧 Backend Integration Checklist

### ✅ What's Ready:
- [x] Clean API service layer
- [x] Error handling & loading states
- [x] Mock/real data switching
- [x] Proper data flow architecture
- [x] Reusable hooks for all components

### 🎯 What You Need to Do:
1. **Update Flask backend** to match the expected endpoints
2. **Set environment variables** to switch from mock to real data
3. **Test each endpoint** - the frontend will handle the rest!

## 🚀 Migration Strategy

### Phase 1: Keep Mock Data
- Develop backend APIs
- Test with Postman/curl
- Frontend keeps working with mocks

### Phase 2: Gradual Integration
```javascript
// Switch one component at a time
const USE_REAL_API_FOR_CURRENT_DATA = true;
```

### Phase 3: Full Integration
```javascript
// Switch everything at once
REACT_APP_USE_MOCK_DATA=false
```

## 💡 Why This Architecture is Great

### ✅ **Separation of Concerns**
- UI components focus on display
- Data services handle API logic
- Easy to test and maintain

### ✅ **Development Friendly**
- Mock data for offline development
- Real APIs for production
- Switch with one environment variable

### ✅ **Error Handling**
- Consistent error states across all components
- Loading states handled automatically
- Retry logic built-in

### ✅ **Scalable**
- Add new endpoints easily
- Reuse hooks across components
- Type-safe with minimal effort

## 🎯 Bottom Line

**The frontend is VERY easy to integrate!** 

Just:
1. Build the Flask endpoints to match `apiService.js`
2. Set `REACT_APP_USE_MOCK_DATA=false`
3. Done! 🎉

The architecture is clean, the data flow is clear, and switching between mock and real data is seamless.
