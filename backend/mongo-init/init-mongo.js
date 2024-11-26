db = db.getSiblingDB('omnipedia');

// Create collections if they don't exist
db.createCollection('requirements');
db.createCollection('evaluations');

// Create indexes if needed
// db.requirements.createIndex({ "field_name": 1 });

// You can add any other initialization logic here
