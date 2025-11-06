/**
 * Reset pending reviews from backup
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
    const db = await connectToDatabase();
    
    // Get all backup reviews
    const backups = await db.collection('backup_reviews').find({}).toArray();
    
    if (!backups || backups.length === 0) {
      return res.status(404).json({ 
        error: 'No backup found. Run seed_mongodb.py first to create backup.' 
      });
    }
    
    // Clear current pending reviews
    await db.collection('pending_reviews').deleteMany({});
    
    // Restore from backup
    await db.collection('pending_reviews').insertMany(backups);
    
    res.json({ 
      success: true,
      count: backups.length,
      message: `Reset ${backups.length} reviews from backup`
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
};

