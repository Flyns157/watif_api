# README: Recommendation Systems for Social Network

This module provides a flexible framework for implementing recommendation systems in a social network. It defines an abstract base class, `recommender_engine`, and three concrete implementations: `MC_engine`, `EM_engine`, and `JA_engine`. These engines implement distinct strategies for recommending users, posts, and threads based on various factors like shared connections, interests, and embeddings.

---

## **Structure**

### **Abstract Base Class: `recommender_engine`**

- Provides a foundation for recommendation systems.
- Contains the following unimplemented methods:
  - `recommend_users`: Suggests users to follow.
  - `recommend_posts`: Suggests posts for engagement.
  - `recommend_threads`: Suggests threads to join.
- Requires a `Database` instance for interaction with Neo4j.

---

## **Engines**

### **1. Monte Carlo Engine (`MC_engine`)**

- **Objective**: Recommends based on explicit relationships such as mutual followers and interests.
- **Key Features**:
  - Combines weights for multiple factors (e.g., follow connections and shared interests) to calculate scores.
  - Recommendations for:
    - **Users**: Based on shared followers (`FOLLOWS`) and overlapping interests (`INTERESTED_BY`).
    - **Posts**: Based on shared interests (`HAS_KEY`) and user interactions (`LIKES`/`COMMENTED_ON`).
    - **Threads**: Based on shared memberships (`MEMBER_OF`) and relevant interests.
- **Design Choices**:
  - **Weighting Mechanism**: Flexibility in adjusting the influence of different factors.
  - **Direct Querying**: Uses Neo4j queries to process relationships efficiently.

---

### **2. Embedding-Based Engine (`EM_engine`)**

- **Objective**: Leverages embeddings to recommend based on semantic similarity.
- **Key Features**:
  - Utilizes `MC_embedder` to generate embeddings for users, posts, and threads.
  - Calculates **cosine similarity** between embeddings to rank entities.
  - Recommendations for:
    - **Users**: Based on similarity in user embeddings.
    - **Posts**: Based on similarity between user and post embeddings.
    - **Threads**: Based on similarity between user and thread embeddings.
- **Design Choices**:
  - **Embedding Storage**: Embeddings are cached in MongoDB to avoid repeated computations.
  - **Scalability**: Embeddings support large-scale similarity computations using `cosine_similarity`.

---

### **3. Interest and Connection Engine (`JA_engine`)**

- **Objective**: Combines mutual connections and interest-based scoring.
- **Key Features**:
  - Extends recommendations with additional metrics like hashtags for user-specific contexts.
  - Focuses on optimizing results for both engagement and interest alignment.
- **Design Choices**:
  - **Flexible Metrics**: Includes hashtags and other user-defined data to enhance personalization.
  - **Simplicity**: Leverages Neo4j queries for direct and interpretable recommendation logic.

---

## **Usage**

1. **Setup**:

   - Initialize a `Database` instance connected to Neo4j and MongoDB.
   - Create an instance of one of the engines:
     ```python
     from recommender_engine import MC_engine, EM_engine, JA_engine, Database

     db = Database()  # Configure database connection
     engine = MC_engine(db)  # Replace with desired engine class
     ```
2. **Generate Recommendations**:

   - Call the desired method:
     ```python
     user_recommendations = engine.recommend_users(user_id="123")
     post_recommendations = engine.recommend_posts(user_id="123")
     thread_recommendations = engine.recommend_threads(user_id="123")
     ```

---

## **Comparison of Choices**

| **Criterion**       | **MC_engine**             | **EM_engine**             | **JA_engine**            |
| ------------------------- | ------------------------------- | ------------------------------- | ------------------------------ |
| **Data Source**     | Explicit relationships in Neo4j | Embedding similarity (MongoDB)  | Neo4j relationships and scores |
| **Scalability**     | Efficient for small graphs      | Optimized for large datasets    | Suitable for moderate graphs   |
| **Personalization** | Customizable weights            | High, using semantic similarity | Moderate, using tags/hashtags  |
| **Use Cases**       | User engagement & connections   | Personalized feeds & discovery  | Interest-driven suggestions    |

---

## **Design Rationales**

1. **Abstraction**: The base class enforces a clear structure, promoting extensibility.
2. **Flexibility**: Weighting systems (e.g., in `MC_engine`) allow fine-tuning recommendations.
3. **Scalability**: Embedding-based approaches (`EM_engine`) support large-scale systems.
4. **Interoperability**: MongoDB and Neo4j integration ensures efficient data storage and querying.

---

## **Future Enhancements**

- **Hybrid Approaches**: Combine explicit relationships and embeddings.
- **Real-Time Updates**: Enhance recommendations with live activity streams.
- **Improved Embeddings**: Use neo4j instead of mongoDB to generate imbedding and use a "range" around the user and don't overload the server
