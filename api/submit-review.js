/**
 * Submit a review to MongoDB
 */
const { MongoClient, ObjectId } = require('mongodb');

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
    
    const client = await connectToDatabase();
    const db = client.db('llm_reviews');
    
    // Save to completed_reviews
    await db.collection('completed_reviews').insertOne({
      ...reviewData,
      submitted_at: new Date()
    });
    
    // Remove from pending_reviews
    if (reviewData.review_id) {
      await db.collection('pending_reviews').deleteOne({
        id: reviewData.review_id
      });
    }
    
    res.json({ success: true });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

