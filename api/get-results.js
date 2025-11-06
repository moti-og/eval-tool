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
    maxIdleTimeMS: 60000
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
    
    // Only get fields we need (MongoDB doesn't allow mixing inclusion and exclusion)
    const reviews = await collection
      .find({}, {
        projection: {
          _id: 1,
          review_id: 1,
          prompt: 1,
          acceptable: 1,
          reviewer: 1,
          notes: 1,
          timestamp: 1,
          submitted_at: 1,
          organization_name: 1,
          agency_user: 1,
          user_id: 1
          // Note: response field excluded by not including it
        }
      })
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

