import "@testing-library/jest-dom/vitest"
import { MotionGlobalConfig } from "motion/react"

// jsdom never paints, so an exit animation would hold its node in the DOM forever
// and every "it closed" assertion would fail. Animations land on their end state
// in one step here; the browser still runs them.
MotionGlobalConfig.skipAnimations = true
