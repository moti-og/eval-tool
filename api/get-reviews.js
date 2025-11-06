/**
 * Get pending reviews from MongoDB
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
    
    // Just get count and first review (faster)
    const [count, firstReview] = await Promise.all([
      collection.countDocuments(),
      collection.findOne({})
    ]);
    
    if (!firstReview) {
      return res.json({ error: 'No reviews available' });
    }
    
    res.json({
      review: firstReview,
      remaining: count,
      total: count
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

