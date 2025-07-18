// MongoDB initialization script for Multi-Agent System

// Switch to the multi_agent_system database
db = db.getSiblingDB('multi_agent_system');

// Create collections with validation
db.createCollection("users", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["user_id", "created_at"],
         properties: {
            user_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            display_name: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            email: {
               bsonType: "string",
               pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
               description: "must be a valid email address if the field exists"
            },
            created_at: {
               bsonType: "string",
               description: "must be an ISO date string and is required"
            },
            updated_at: {
               bsonType: "string",
               description: "must be an ISO date string"
            },
            is_active: {
               bsonType: "bool",
               description: "must be a boolean"
            },
            last_login: {
               bsonType: "string",
               description: "must be an ISO date string if the field exists"
            },
            preferences: {
               bsonType: "object",
               description: "must be an object if the field exists"
            }
         }
      }
   }
});

db.createCollection("chat_sessions", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["session_id", "user_id", "created_at"],
         properties: {
            session_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            user_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            title: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            created_at: {
               bsonType: "string",
               description: "must be an ISO date string and is required"
            },
            updated_at: {
               bsonType: "string",
               description: "must be an ISO date string"
            },
            is_active: {
               bsonType: "bool",
               description: "must be a boolean"
            },
            total_messages: {
               bsonType: "int",
               minimum: 0,
               description: "must be a non-negative integer"
            },
            session_metadata: {
               bsonType: "object",
               description: "must be an object if the field exists"
            }
         }
      }
   }
});

db.createCollection("chat_messages", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["message_id", "session_id", "user_input", "created_at"],
         properties: {
            message_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            session_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            user_input: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            agent_response: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            detected_intents: {
               bsonType: "array",
               description: "must be an array if the field exists"
            },
            primary_intent: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            processing_mode: {
               bsonType: "string",
               enum: ["single", "parallel"],
               description: "must be either 'single' or 'parallel' if the field exists"
            },
            agent_results: {
               bsonType: "object",
               description: "must be an object if the field exists"
            },
            execution_summary: {
               bsonType: "object",
               description: "must be an object if the field exists"
            },
            created_at: {
               bsonType: "string",
               description: "must be an ISO date string and is required"
            },
            processing_time: {
               bsonType: "int",
               minimum: 0,
               description: "must be a non-negative integer if the field exists"
            },
            errors: {
               bsonType: "array",
               description: "must be an array if the field exists"
            },
            success: {
               bsonType: "bool",
               description: "must be a boolean"
            }
         }
      }
   }
});

db.createCollection("system_logs", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["log_id", "timestamp", "level", "component", "message"],
         properties: {
            log_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            timestamp: {
               bsonType: "string",
               description: "must be an ISO date string and is required"
            },
            level: {
               bsonType: "string",
               enum: ["DEBUG", "INFO", "WARNING", "ERROR"],
               description: "must be a valid log level and is required"
            },
            component: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            message: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            user_id: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            session_id: {
               bsonType: "string",
               description: "must be a string if the field exists"
            },
            additional_data: {
               bsonType: "object",
               description: "must be an object if the field exists"
            }
         }
      }
   }
});

// Create indexes for better performance
print("Creating indexes...");

// Users collection indexes
db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });
db.users.createIndex({ "created_at": 1 });
db.users.createIndex({ "is_active": 1 });

// Chat sessions collection indexes
db.chat_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.chat_sessions.createIndex({ "user_id": 1 });
db.chat_sessions.createIndex({ "user_id": 1, "updated_at": -1 });
db.chat_sessions.createIndex({ "created_at": 1 });
db.chat_sessions.createIndex({ "is_active": 1 });

// Chat messages collection indexes
db.chat_messages.createIndex({ "message_id": 1 }, { unique: true });
db.chat_messages.createIndex({ "session_id": 1 });
db.chat_messages.createIndex({ "session_id": 1, "created_at": 1 });
db.chat_messages.createIndex({ "primary_intent": 1 });
db.chat_messages.createIndex({ "processing_mode": 1 });
db.chat_messages.createIndex({ "success": 1 });
db.chat_messages.createIndex({ "created_at": 1 });

// System logs collection indexes
db.system_logs.createIndex({ "log_id": 1 }, { unique: true });
db.system_logs.createIndex({ "timestamp": -1 });
db.system_logs.createIndex({ "level": 1 });
db.system_logs.createIndex({ "component": 1 });
db.system_logs.createIndex({ "user_id": 1 }, { sparse: true });
db.system_logs.createIndex({ "session_id": 1 }, { sparse: true });

print("MongoDB initialization completed successfully!");
print("Collections created: users, chat_sessions, chat_messages, system_logs");
print("Indexes created for optimal performance");

// Insert a test document to verify everything works
db.system_logs.insertOne({
   log_id: "init-" + new Date().getTime(),
   timestamp: new Date().toISOString(),
   level: "INFO",
   component: "mongodb-init",
   message: "MongoDB database initialized successfully",
   additional_data: {
      collections_created: ["users", "chat_sessions", "chat_messages", "system_logs"],
      indexes_created: true,
      initialization_time: new Date().toISOString()
   }
});

print("Test log entry created successfully!");
