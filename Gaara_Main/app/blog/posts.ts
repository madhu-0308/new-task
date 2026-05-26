export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: string;
  body: string[];
}

export const POSTS: BlogPost[] = [
  {
    slug: "real-time-pose-recognition-mediapipe-lstm",
    title: "Real-time pose recognition with MediaPipe and LSTM",
    excerpt:
      "How we built a 30fps coaching pipeline that runs entirely in the browser — and the engineering trade-offs we made along the way.",
    date: "October 2025",
    readTime: "7 min read",
    category: "Engineering",
    body: [
      "When we set out to build Gaara AI, the goal was simple: deliver coach-grade biomechanical feedback in real time, on any device, with no installs. Six months later, we have a pipeline that processes 30 video frames per second through a MediaPipe Holistic model and an LSTM classifier — all in your browser.",
      "MediaPipe Holistic gives us 33 pose landmarks, 21 hand landmarks per hand, and 468 face landmarks per frame. That's 1,662 numerical features per frame. The LSTM operates on a sliding window of 30 frames, classifying body movements in <250ms.",
      "The trickiest part wasn't the ML — it was the engineering trade-offs. Run inference too often and the browser stutters. Run it too rarely and feedback feels laggy. We landed on a 250ms cadence with a 3-frame stable-detection guard, which feels instant but doesn't burn CPU when the body isn't moving.",
      "Privacy was non-negotiable from day one. Raw video frames never leave the device. Only the 1,662-dimensional feature vector is sent to our API for inference. This kept us simple from a regulatory standpoint and made users far more comfortable practising at home.",
      "If you're building anything similar, our biggest lesson: invest early in the stable-detection logic. The model will produce noise. Filtering it intelligently is what makes the product feel premium.",
    ],
  },
  {
    slug: "form-score-vs-pose-duration",
    title: "Why your yoga form score matters more than how long you hold the pose",
    excerpt:
      "Most fitness apps reward time. We reward form. Here's why correct biomechanics is the only metric that drives real progress.",
    date: "September 2025",
    readTime: "5 min read",
    category: "Coaching",
    body: [
      "Open most yoga apps and they'll tell you to hold a pose for 30 seconds. Hold it for 60? Even better. The implicit assumption is that duration equals progress.",
      "It doesn't. If your hips are tilted in Warrior II, holding it for two minutes just reinforces a flawed pattern — and increases your injury risk. Time without alignment is time wasted (or worse).",
      "That's why Gaara AI scores form, not duration. Every pose gets a score out of 100 across 5 biomechanical criteria: hip alignment, weight distribution, arm extension, knee position, and spinal lift.",
      "The result? Users who track their form score consistently see measurable progress within two weeks — going from average scores in the 50s to the high 80s. Not by holding poses longer, but by fixing the small alignment errors the AI flags every session.",
      "The real shift is mental. When you stop optimising for 'how long' and start optimising for 'how well', you train smarter — and your body thanks you for it.",
    ],
  },
  {
    slug: "from-research-lab-to-webcam",
    title: "From research lab to webcam: democratising biomechanics",
    excerpt:
      "Pose analysis used to require a $50k motion-capture lab. Now it runs on your phone. Here's how we got here — and what it means for sports.",
    date: "August 2025",
    readTime: "6 min read",
    category: "Industry",
    body: [
      "A decade ago, getting a biomechanical breakdown of your batting technique meant booking time at a sports science lab. Reflective markers, multi-camera setups, post-processing — all to tell you your front knee bend was 5 degrees off.",
      "Today, the same analysis runs in your browser using a $30 webcam. The technology that powered Olympic athletes is now in the hands of any club cricketer or yoga student.",
      "The key shift was deep learning. MediaPipe and similar models learned to extract precise body landmarks from ordinary 2D video — something that used to require physical markers and stereo cameras. The accuracy now rivals lab-grade systems for most use cases.",
      "What this unlocks is staggering. A 14-year-old in a small town can get the same coaching feedback as a national-level player. A yoga student can correct her form without paying for a private instructor. The cost of expert biomechanical advice has effectively dropped to zero.",
      "We're at the start of a coaching revolution. Over the next five years, AI coaching will expand into tennis, golf, swimming, weightlifting — anywhere movement matters. Gaara AI is just one player in this future. We're excited to build it.",
    ],
  },
];

export function getPost(slug: string): BlogPost | undefined {
  return POSTS.find((p) => p.slug === slug);
}
