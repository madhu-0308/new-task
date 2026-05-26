import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, type Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

function hasFirebaseConfig(): boolean {
  const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY?.trim();
  return Boolean(apiKey && apiKey.length > 10);
}

export const isFirebaseConfigured = hasFirebaseConfig();

let app: FirebaseApp | null = null;

if (isFirebaseConfigured) {
  app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
}

export const auth: Auth | null = app ? getAuth(app) : null;
export const googleProvider: GoogleAuthProvider | null = app
  ? new GoogleAuthProvider()
  : null;
