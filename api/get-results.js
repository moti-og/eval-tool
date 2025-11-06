/**
 * Get completed reviews from MongoDB for analytics
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
    const collection = db.collection('completed_reviews');
    
    // Get all fields including response (needed for expanded view)
    const reviews = await collection
      .find({})
      .sort({ submitted_at: -1 })
      .limit(100)
      .toArray();
    
    if (!reviews || reviews.length === 0) {
      return res.json({ error: 'No reviews yet' });
    }
    
    res.json({ reviews });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

