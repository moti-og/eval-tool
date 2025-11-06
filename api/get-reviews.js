/**
 * Get pending reviews from MongoDB
 */
const { MongoClient } = require('mongodb');

let cachedClient = null;

async function connectToDatabase() {
  if (cachedClient) {
    return cachedClient;
  }
  
  const client = await MongoClient.connect(process.env.MONGODB_URI);
  cachedClient = client;
  return client;
}

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Content-Type', 'application/json');
  
  try {
    const client = await connectToDatabase();
    const db = client.db('llm_reviews');
    const collection = db.collection('pending_reviews');
    
    // Get all pending reviews
    const reviews = await collection.find({}).limit(100).toArray();
    
    if (!reviews || reviews.length === 0) {
      return res.json({ error: 'No reviews available' });
    }
    
    // Return first review with count
    res.json({
      review: reviews[0],
      remaining: reviews.length,
      total: reviews.length
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

