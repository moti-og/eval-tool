/**
 * Serverless function to serve MongoDB Data API configuration
 * This is the ONLY serverless function needed - just returns config
 */

module.exports = (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Content-Type', 'application/json');
  
  // Return config from environment variables
  res.json({
    apiUrl: process.env.MONGODB_DATA_API_URL || '',
    apiKey: process.env.MONGODB_API_KEY || '',
    dataSource: 'Cluster0',
    database: 'llm_reviews',
    pendingCollection: 'pending_reviews',
    completedCollection: 'completed_reviews'
  });
};

