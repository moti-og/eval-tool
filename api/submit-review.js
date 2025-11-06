/**
 * Submit a review to MongoDB
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
    maxIdleTimeMS: 60000
  });
  
  cachedClient = client;
  cachedDb = client.db('llm_reviews');
  return cachedDb;
}

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Content-Type', 'application/json');
  
  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const reviewData = req.body;
    
    const db = await connectToDatabase();
    
    // Parallel operations for speed
    await Promise.all([
      db.collection('completed_reviews').insertOne({
        ...reviewData,
        submitted_at: new Date()
      }),
      reviewData.review_id ? 
        db.collection('pending_reviews').deleteOne({ id: reviewData.review_id }) :
        Promise.resolve()
    ]);
    
    res.json({ success: true });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

