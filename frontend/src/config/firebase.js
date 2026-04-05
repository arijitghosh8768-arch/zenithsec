import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyB0r9vO5YcVRCYUUxjojCkxDnEGbStUFPM",
  authDomain: "zenithsec-52df5.firebaseapp.com",
  projectId: "zenithsec-52df5",
  storageBucket: "zenithsec-52df5.firebasestorage.app",
  messagingSenderId: "139676942448",
  appId: "1:139676942448:web:5f4d2bd1889931c8d374b5",
  measurementId: "G-KNYN81M0SP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;
