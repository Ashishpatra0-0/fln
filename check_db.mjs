import { MongoClient } from 'mongodb';

async function check() {
  const uri = 'mongodb+srv://itsashish345_db_user:dPYQyjRu4GCnbIav@cluster0.cxi0hf3.mongodb.net/fln_platform?retryWrites=true&w=majority';
  const client = new MongoClient(uri);
  await client.connect();
  const db = client.db();
  console.log('Connected to:', db.databaseName);

  const collections = await db.listCollections().toArray();
  console.log('Collections:', collections.map(c => c.name));

  for (const c of collections) {
    const count = await db.collection(c.name).countDocuments();
    console.log(`${c.name}: ${count}`);
  }
  await client.close();
}

check().catch(console.error);
