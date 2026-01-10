/**
 * [INPUT]: 依赖 framer-motion 的 motion 值类型
 * [OUTPUT]: 对外提供 Apple 级 Spring 物理引擎动画预设
 * [POS]: lib/ 动画配置库，被所有页面和组件消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { Variants, Transition } from 'framer-motion'

/* ========================================
   Apple 风格 Spring 配置
   核心哲学: Spring 弹簧 + 阻尼落定 + 物理惯性
   ======================================== */

export const springPresets = {
  // 标准交互 - 按钮、卡片 hover (~200ms)
  snappy: { type: "spring", stiffness: 400, damping: 30 } as Transition,

  // 柔和过渡 - 面板展开、模态框 (~350ms)
  gentle: { type: "spring", stiffness: 300, damping: 35 } as Transition,

  // 弹性强调 - 成功反馈、关键元素 (~300ms)
  bouncy: { type: "spring", stiffness: 500, damping: 25, mass: 0.8 } as Transition,

  // 优雅落定 - 页面过渡、大元素移动 (~500ms)
  smooth: { type: "spring", stiffness: 200, damping: 40, mass: 1.2 } as Transition,

  // 惯性滑动 - 列表、轮播
  inertia: { type: "spring", stiffness: 150, damping: 20, mass: 0.5 } as Transition
}

/* ========================================
   视口触发配置
   ======================================== */

export const viewportConfig = {
  once: true,
  margin: "-100px"
}

/* ========================================
   Apple 缓动曲线（非 Spring 场景）
   ======================================== */

export const appleEase = [0.25, 0.1, 0.25, 1.0] // iOS 标准曲线
export const appleEaseOut = [0.22, 1, 0.36, 1] // iOS 弹出曲线
export const appleDecelerate = [0, 0, 0.2, 1] // iOS 减速曲线

/* ========================================
   Spring 动画预设（Apple 级）
   ======================================== */

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30
    }
  }
}

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30
    }
  }
}

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 350,
      damping: 32
    }
  }
}

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 350,
      damping: 32
    }
  }
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25
    }
  }
}

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1
    }
  }
}

export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04,
      delayChildren: 0.08
    }
  }
}

/* ========================================
   特殊动画预设
   ======================================== */

export const slideInBottom: Variants = {
  hidden: { opacity: 0, y: 100 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 260,
      damping: 40
    }
  }
}

export const zoomIn: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 28
    }
  }
}

/* ========================================
   交互动画预设（Apple Card 效果）
   ======================================== */

export const hoverLift = {
  rest: {
    scale: 1,
    y: 0,
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
  },
  hover: {
    scale: 1.02,
    y: -4,
    boxShadow: "0 12px 32px rgba(0,0,0,0.15)",
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25
    }
  }
}

export const tapScale = {
  rest: { scale: 1 },
  pressed: {
    scale: 0.96,
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 30
    }
  }
}

/* ========================================
   模态框动画（优雅落定）
   ======================================== */

export const modalOverlay = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.2 }
  }
}

export const modalContent = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 35
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.15 }
  }
}

/* ========================================
   页面路由过渡
   ======================================== */

export const pageTransition = {
  initial: { opacity: 0, x: 20 },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25
    }
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25
    }
  }
}

/* ========================================
   装饰性动画
   ======================================== */

export const floatAnimation = {
  initial: { y: 0 },
  animate: {
    y: [-10, 10, -10],
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 10,
      repeat: Infinity
    }
  }
}

export const pulseGlow = {
  initial: { opacity: 0.5 },
  animate: {
    opacity: [0.5, 1, 0.5],
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 15,
      repeat: Infinity
    }
  }
}

/* ========================================
   数字计数动画
   ======================================== */

export const counterAnimation = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  transition: {
    type: "spring",
    stiffness: 500,
    damping: 30
  }
}

/* ========================================
   路径绘制动画（用于 SVG）
   ======================================== */

export const pathDraw = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: { type: "spring", stiffness: 200, damping: 40 },
      opacity: { duration: 0.3 }
    }
  }
}

/* ========================================
   旋转动画
   ======================================== */

export const rotate360 = {
  animate: {
    rotate: 360,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 20,
      repeat: Infinity,
      repeatDelay: 0
    }
  }
}

/* ========================================
   弹跳动画
   ======================================== */

export const bounce = {
  animate: {
    y: [0, -20, 0],
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 10,
      repeat: Infinity
    }
  }
}

export const bounceSubtle = {
  animate: {
    y: [0, -5, 0],
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 15,
      repeat: Infinity
    }
  }
}

/* ========================================
   闪烁动画
   ======================================== */

export const blink = {
  animate: {
    opacity: [1, 0.5, 1],
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 20,
      repeat: Infinity
    }
  }
}

/* ========================================
   导出所有预设
   ======================================== */

export const motionPresets = {
  // Spring 配置
  springPresets,

  // 缓动曲线
  appleEase,
  appleEaseOut,
  appleDecelerate,

  // 基础动画
  fadeInUp,
  fadeInDown,
  fadeInLeft,
  fadeInRight,
  scaleIn,
  slideInBottom,
  zoomIn,

  // 容器动画
  staggerContainer,
  staggerContainerFast,

  // 交互动画
  hoverLift,
  tapScale,

  // 模态框
  modalOverlay,
  modalContent,

  // 页面过渡
  pageTransition,

  // 视口触发
  viewportConfig,

  // 装饰动画
  floatAnimation,
  pulseGlow,
  counterAnimation,
  pathDraw,
  rotate360,
  bounce,
  bounceSubtle,
  blink
}

export default motionPresets

