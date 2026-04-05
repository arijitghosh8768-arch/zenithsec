// File: frontend/src/services/firebaseService.js

import { db, auth, storage } from '../config/firebase';
import { 
  collection, 
  addDoc, 
  getDocs, 
  getDoc, 
  updateDoc, 
  deleteDoc, 
  doc, 
  query, 
  where, 
  orderBy, 
  limit,
  serverTimestamp,
  increment 
} from "firebase/firestore";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged 
} from "firebase/auth";
import { ref, uploadBytes, getDownloadURL } from "firebase/storage";

// ============= AUTHENTICATION =============

export const registerUser = async (email, password, userData) => {
  try {
    // Create auth user
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Save user data to Firestore
    await addDoc(collection(db, "users"), {
      uid: user.uid,
      email: email,
      username: userData.username,
      skillLevel: userData.skillLevel || 'beginner',
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp()
    });
    
    return { success: true, user };
  } catch (error) {
    console.error("Registration error:", error);
    return { success: false, error: error.message };
  }
};

export const loginUser = async (email, password) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { success: true, user: userCredential.user };
  } catch (error) {
    console.error("Login error:", error);
    return { success: false, error: error.message };
  }
};

export const logoutUser = async () => {
  try {
    await signOut(auth);
    return { success: true };
  } catch (error) {
    console.error("Logout error:", error);
    return { success: false, error: error.message };
  }
};

export const getCurrentUser = () => {
  return new Promise((resolve) => {
    onAuthStateChanged(auth, (user) => {
      resolve(user);
    });
  });
};

// ============= CHAT SESSIONS =============

export const saveChatSession = async (userId, sessionData) => {
  try {
    const docRef = await addDoc(collection(db, "chatSessions"), {
      userId: userId,
      title: sessionData.title || "New Chat",
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      messageCount: 0
    });
    return { success: true, id: docRef.id };
  } catch (error) {
    console.error("Save session error:", error);
    return { success: false, error: error.message };
  }
};

export const getChatSessions = async (userId) => {
  try {
    const q = query(
      collection(db, "chatSessions"),
      where("userId", "==", userId),
      orderBy("updatedAt", "desc")
    );
    const querySnapshot = await getDocs(q);
    const sessions = [];
    querySnapshot.forEach((doc) => {
      sessions.push({ id: doc.id, ...doc.data() });
    });
    return { success: true, sessions };
  } catch (error) {
    console.error("Get sessions error:", error);
    return { success: false, error: error.message, sessions: [] };
  }
};

// ============= CHAT MESSAGES =============

export const saveChatMessage = async (sessionId, messageData) => {
  try {
    await addDoc(collection(db, "chatMessages"), {
      sessionId: sessionId,
      role: messageData.role,
      content: messageData.content,
      timestamp: serverTimestamp(),
      tokensUsed: messageData.tokensUsed || 0
    });
    
    // Update session message count
    const sessionRef = doc(db, "chatSessions", sessionId);
    await updateDoc(sessionRef, {
      messageCount: increment(1),
      updatedAt: serverTimestamp()
    });
    
    return { success: true };
  } catch (error) {
    console.error("Save message error:", error);
    return { success: false, error: error.message };
  }
};

export const getChatMessages = async (sessionId) => {
  try {
    const q = query(
      collection(db, "chatMessages"),
      where("sessionId", "==", sessionId),
      orderBy("timestamp", "asc")
    );
    const querySnapshot = await getDocs(q);
    const messages = [];
    querySnapshot.forEach((doc) => {
      messages.push({ id: doc.id, ...doc.data() });
    });
    return { success: true, messages };
  } catch (error) {
    console.error("Get messages error:", error);
    return { success: false, error: error.message, messages: [] };
  }
};

// ============= USER PROGRESS =============

export const updateUserProgress = async (userId, topic, score) => {
  try {
    const q = query(
      collection(db, "userProgress"),
      where("userId", "==", userId),
      where("topic", "==", topic)
    );
    const querySnapshot = await getDocs(q);
    
    if (querySnapshot.empty) {
      // Create new progress
      await addDoc(collection(db, "userProgress"), {
        userId: userId,
        topic: topic,
        score: score,
        completedAt: serverTimestamp()
      });
    } else {
      // Update existing progress
      const docRef = doc(db, "userProgress", querySnapshot.docs[0].id);
      await updateDoc(docRef, {
        score: score,
        completedAt: serverTimestamp()
      });
    }
    
    return { success: true };
  } catch (error) {
    console.error("Update progress error:", error);
    return { success: false, error: error.message };
  }
};

export const getUserProgress = async (userId) => {
  try {
    const q = query(
      collection(db, "userProgress"),
      where("userId", "==", userId)
    );
    const querySnapshot = await getDocs(q);
    const progress = [];
    querySnapshot.forEach((doc) => {
      progress.push({ id: doc.id, ...doc.data() });
    });
    return { success: true, progress };
  } catch (error) {
    console.error("Get progress error:", error);
    return { success: false, error: error.message, progress: [] };
  }
};

// ============= CERTIFICATES =============

export const saveCertificate = async (userId, certificateData) => {
  try {
    const docRef = await addDoc(collection(db, "certificates"), {
      userId: userId,
      title: certificateData.title,
      blockchainHash: certificateData.blockchainHash,
      issuedAt: serverTimestamp(),
      metadata: certificateData.metadata || {}
    });
    return { success: true, id: docRef.id };
  } catch (error) {
    console.error("Save certificate error:", error);
    return { success: false, error: error.message };
  }
};

export const getUserCertificates = async (userId) => {
  try {
    const q = query(
      collection(db, "certificates"),
      where("userId", "==", userId),
      orderBy("issuedAt", "desc")
    );
    const querySnapshot = await getDocs(q);
    const certificates = [];
    querySnapshot.forEach((doc) => {
      certificates.push({ id: doc.id, ...doc.data() });
    });
    return { success: true, certificates };
  } catch (error) {
    console.error("Get certificates error:", error);
    return { success: false, error: error.message, certificates: [] };
  }
};

// ============= FILE UPLOAD =============

export const uploadFile = async (file, userId, folder = "scans") => {
  try {
    const storageRef = ref(storage, `${folder}/${userId}/${Date.now()}_${file.name}`);
    await uploadBytes(storageRef, file);
    const downloadURL = await getDownloadURL(storageRef);
    return { success: true, url: downloadURL, path: storageRef.fullPath };
  } catch (error) {
    console.error("Upload error:", error);
    return { success: false, error: error.message };
  }
};
