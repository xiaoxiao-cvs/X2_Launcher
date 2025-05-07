/**
 * Vue 工具函数
 * 这个文件主要用于处理Vue 3相关的辅助函数和工具方法
 */

/**
 * 用于解决Vue编译器宏警告的辅助函数
 * 
 * 注意：这些函数应用于解决静态分析工具报错，实际上不会在运行时被调用
 * defineProps, defineEmits, defineExpose 和 withDefaults 是Vue编译器宏，
 * 不需要导入，但一些静态分析工具可能会报告它们为未定义
 */
export const setupCompilerMacros = () => {
  // 这个函数只是为了解决编辑器警告，不会真正执行
  // 实际的编译器宏在Vue SFC中会由Vue编译器处理
  if (false) { // 防止被打包工具优化掉
    // eslint-disable-next-line no-undef
    defineProps({});
    // eslint-disable-next-line no-undef
    defineEmits([]);
    // eslint-disable-next-line no-undef
    defineExpose({});
    // eslint-disable-next-line no-undef
    withDefaults(defineProps({}), {});
  }
};

/**
 * 创建一个防抖函数
 * @param {Function} fn 要执行的函数
 * @param {number} delay 延迟时间 (毫秒)
 * @returns {Function} 防抖后的函数
 */
export const debounce = (fn, delay = 300) => {
  let timer = null;
  return function(...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
};

/**
 * 创建一个节流函数
 * @param {Function} fn 要执行的函数
 * @param {number} limit 限制时间 (毫秒)
 * @returns {Function} 节流后的函数
 */
export const throttle = (fn, limit = 300) => {
  let lastCall = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      fn.apply(this, args);
    }
  };
};
