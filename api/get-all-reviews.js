/**
 * Get ALL pending reviews from MongoDB at once
 * This allows the frontend to keep them in memory for instant navigation
 */
const { MongoClient } = require('mongodb');

let cachedClient = null;
let cachedDb = null;

async function connectToDatabase() {
  if (cachedClient && cachedDb) {
    return cachedDb;
  }
  
  const client = await MongoClient.connect(process.env.MONGODB_URI, {
    maxPoolSize: 1,
    minPoolSize: 1,
    maxIdleTimeMS: 60000,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 10000,
    connectTimeoutMS: 10000
  });
  
  cachedClient = client;
  cachedDb = client.db('llm_reviews');
  return cachedDb;
}

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Content-Type', 'application/json');
  
  try {
    const db = await connectToDatabase();
    const collection = db.collection('pending_reviews');
    
    // Get ALL pending reviews (they're already filtered to ~10 items max)
    const reviews = await collection.find({}).toArray();
    
    if (!reviews || reviews.length === 0) {
      return res.json({ error: 'No reviews available' });
    }
    
    // Return all reviews for client-side memory storage
    res.json({
      reviews: reviews,
      total: reviews.length
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

