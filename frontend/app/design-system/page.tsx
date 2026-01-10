// Input: shadcn/ui 组件库
// Output: 设计系统组件展示页面（展示所有 30+ shadcn 组件）
// Position: 设计系统文档页面，供开发者查阅组件使用方法
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronRight, AlertCircle, Check, Info, Plus, Settings, User, Search, Bell } from 'lucide-react'

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Design System
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                shadcn/ui 组件库展示与使用指南
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 mt-4">
            <Badge variant="outline">30+ Components</Badge>
            <Badge variant="outline">TailwindCSS</Badge>
            <Badge variant="outline">TypeScript</Badge>
            <Badge variant="outline">Accessible</Badge>
          </div>
        </div>

        {/* Components Grid */}
        <ScrollArea className="h-[calc(100vh-200px)]">
          <div className="space-y-8 pr-4">
            {/* Core Interactive Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mr-3">
                  1
                </span>
                核心交互组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Button */}
                <Card>
                  <CardHeader>
                    <CardTitle>Button</CardTitle>
                    <CardDescription>按钮组件，支持多种变体</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="default">默认</Button>
                      <Button variant="secondary">次要</Button>
                      <Button variant="destructive">破坏</Button>
                      <Button variant="outline">轮廓</Button>
                      <Button variant="ghost">幽灵</Button>
                      <Button variant="link">链接</Button>
                    </div>
                    <Button size="sm">小号</Button>
                    <Button size="default">默认</Button>
                    <Button size="lg">大号</Button>
                  </CardContent>
                </Card>

                {/* Input */}
                <Card>
                  <CardHeader>
                    <CardTitle>Input</CardTitle>
                    <CardDescription>输入框组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="input-1">默认输入框</Label>
                      <Input id="input-1" placeholder="请输入内容..." />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="input-2">禁用状态</Label>
                      <Input id="input-2" disabled placeholder="禁用输入框" />
                    </div>
                  </CardContent>
                </Card>

                {/* Label */}
                <Card>
                  <CardHeader>
                    <CardTitle>Label</CardTitle>
                    <CardDescription>表单标签组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <Label>默认标签</Label>
                      <Label htmlFor="label-1">关联输入框</Label>
                      <Input id="label-1" />
                    </div>
                  </CardContent>
                </Card>

                {/* Card */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>Card</CardTitle>
                    <CardDescription>卡片组件，用于内容分组</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardHeader>
                          <CardTitle>卡片标题</CardTitle>
                          <CardDescription>卡片描述文本</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <p>这是卡片内容区域，可以放置任何内容。</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader>
                          <CardTitle>带操作的卡片</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p>卡片内容</p>
                          <div className="flex gap-2 mt-4">
                            <Button size="sm">确认</Button>
                            <Button size="sm" variant="outline">取消</Button>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </CardContent>
                </Card>

                {/* Dialog */}
                <Card>
                  <CardHeader>
                    <CardTitle>Dialog</CardTitle>
                    <CardDescription>对话框组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline">打开对话框</Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>对话框标题</DialogTitle>
                          <DialogDescription>
                            这是对话框描述内容，用于解释对话框的用途。
                          </DialogDescription>
                        </DialogHeader>
                        <div className="py-4">
                          对话框主要内容区域...
                        </div>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>

                {/* Sheet */}
                <Card>
                  <CardHeader>
                    <CardTitle>Sheet</CardTitle>
                    <CardDescription>侧边抽屉组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Sheet>
                      <SheetTrigger asChild>
                        <Button variant="outline">打开侧边栏</Button>
                      </SheetTrigger>
                      <SheetContent>
                        <SheetHeader>
                          <SheetTitle>侧边栏标题</SheetTitle>
                          <SheetDescription>
                            侧边栏描述内容
                          </SheetDescription>
                        </SheetHeader>
                        <div className="py-4">
                          侧边栏内容...
                        </div>
                      </SheetContent>
                    </Sheet>
                  </CardContent>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Form Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mr-3">
                  2
                </span>
                表单组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Select */}
                <Card>
                  <CardHeader>
                    <CardTitle>Select</CardTitle>
                    <CardDescription>下拉选择组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="选择选项" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">选项 1</SelectItem>
                        <SelectItem value="2">选项 2</SelectItem>
                        <SelectItem value="3">选项 3</SelectItem>
                      </SelectContent>
                    </Select>
                  </CardContent>
                </Card>

                {/* Checkbox */}
                <Card>
                  <CardHeader>
                    <CardTitle>Checkbox</CardTitle>
                    <CardDescription>复选框组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox id="terms" />
                      <Label htmlFor="terms">同意条款</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="newsletter" defaultChecked />
                      <Label htmlFor="newsletter">订阅新闻</Label>
                    </div>
                  </CardContent>
                </Card>

                {/* RadioGroup */}
                <Card>
                  <CardHeader>
                    <CardTitle>RadioGroup</CardTitle>
                    <CardDescription>单选框组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RadioGroup defaultValue="option1">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="option1" id="r1" />
                        <Label htmlFor="r1">选项 1</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="option2" id="r2" />
                        <Label htmlFor="r2">选项 2</Label>
                      </div>
                    </RadioGroup>
                  </CardContent>
                </Card>

                {/* Switch */}
                <Card>
                  <CardHeader>
                    <CardTitle>Switch</CardTitle>
                    <CardDescription>开关组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="switch1">通知</Label>
                      <Switch id="switch1" />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="switch2">暗色模式</Label>
                      <Switch id="switch2" defaultChecked />
                    </div>
                  </CardContent>
                </Card>

                {/* Textarea */}
                <Card>
                  <CardHeader>
                    <CardTitle>Textarea</CardTitle>
                    <CardDescription>多行文本输入</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Textarea placeholder="请输入多行文本..." />
                  </CardContent>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Feedback Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center mr-3">
                  3
                </span>
                反馈组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Alert */}
                <Card>
                  <CardHeader>
                    <CardTitle>Alert</CardTitle>
                    <CardDescription>警告提示组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>提示</AlertTitle>
                      <AlertDescription>
                        这是一条重要提示信息。
                      </AlertDescription>
                    </Alert>
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>错误</AlertTitle>
                      <AlertDescription>
                        发生错误，请稍后重试。
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>

                {/* Badge */}
                <Card>
                  <CardHeader>
                    <CardTitle>Badge</CardTitle>
                    <CardDescription>徽章标签组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      <Badge>默认</Badge>
                      <Badge variant="secondary">次要</Badge>
                      <Badge variant="outline">轮廓</Badge>
                      <Badge variant="destructive">破坏</Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Skeleton */}
                <Card>
                  <CardHeader>
                    <CardTitle>Skeleton</CardTitle>
                    <CardDescription>加载骨架屏</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardContent>
                </Card>

                {/* Progress */}
                <Card>
                  <CardHeader>
                    <CardTitle>Progress</CardTitle>
                    <CardDescription>进度条组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Progress value={33} />
                    <Progress value={66} />
                    <Progress value={100} />
                  </CardContent>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Navigation Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mr-3">
                  4
                </span>
                导航组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Tabs */}
                <Card>
                  <CardHeader>
                    <CardTitle>Tabs</CardTitle>
                    <CardDescription>标签页组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Tabs defaultValue="tab1">
                      <TabsList>
                        <TabsTrigger value="tab1">标签 1</TabsTrigger>
                        <TabsTrigger value="tab2">标签 2</TabsTrigger>
                        <TabsTrigger value="tab3">标签 3</TabsTrigger>
                      </TabsList>
                      <TabsContent value="tab1" className="mt-4">
                        标签 1 内容
                      </TabsContent>
                      <TabsContent value="tab2" className="mt-4">
                        标签 2 内容
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>

                {/* Accordion */}
                <Card>
                  <CardHeader>
                    <CardTitle>Accordion</CardTitle>
                    <CardDescription>手风琴折叠组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible>
                      <AccordionItem value="item-1">
                        <AccordionTrigger>项目 1</AccordionTrigger>
                        <AccordionContent>
                          项目 1 的详细内容...
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-2">
                        <AccordionTrigger>项目 2</AccordionTrigger>
                        <AccordionContent>
                          项目 2 的详细内容...
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </CardContent>
                </Card>

                {/* DropdownMenu */}
                <Card>
                  <CardHeader>
                    <CardTitle>DropdownMenu</CardTitle>
                    <CardDescription>下拉菜单组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline">打开菜单</Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuLabel>我的账户</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>个人资料</DropdownMenuItem>
                        <DropdownMenuItem>设置</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>退出登录</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </CardContent>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Display Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-pink-100 dark:bg-pink-900/30 rounded-lg flex items-center justify-center mr-3">
                  5
                </span>
                展示组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Avatar */}
                <Card>
                  <CardHeader>
                    <CardTitle>Avatar</CardTitle>
                    <CardDescription>头像组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center space-x-4">
                      <Avatar>
                        <AvatarImage src="https://github.com/shadcn.png" />
                        <AvatarFallback>CN</AvatarFallback>
                      </Avatar>
                      <Avatar>
                        <AvatarFallback>用户</AvatarFallback>
                      </Avatar>
                    </div>
                  </CardContent>
                </Card>

                {/* Table */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>Table</CardTitle>
                    <CardDescription>表格组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>姓名</TableHead>
                          <TableHead>邮箱</TableHead>
                          <TableHead>角色</TableHead>
                          <TableHead>状态</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell>张三</TableCell>
                          <TableCell>zhangsan@example.com</TableCell>
                          <TableCell>管理员</TableCell>
                          <TableCell><Badge>活跃</Badge></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>李四</TableCell>
                          <TableCell>lisi@example.com</TableCell>
                          <TableCell>用户</TableCell>
                          <TableCell><Badge variant="secondary">离线</Badge></TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>

                {/* Popover */}
                <Card>
                  <CardHeader>
                    <CardTitle>Popover</CardTitle>
                    <CardDescription>弹出框组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="outline">打开弹出框</Button>
                      </PopoverTrigger>
                      <PopoverContent>
                        <div className="space-y-2">
                          <h4 className="font-medium">弹出框标题</h4>
                          <p className="text-sm text-gray-500">
                            弹出框内容描述
                          </p>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </CardContent>
                </Card>

                {/* Tooltip */}
                <Card>
                  <CardHeader>
                    <CardTitle>Tooltip</CardTitle>
                    <CardDescription>工具提示组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline">悬停查看提示</Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>这是工具提示内容</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </CardContent>
                </Card>

                {/* HoverCard */}
                <Card>
                  <CardHeader>
                    <CardTitle>HoverCard</CardTitle>
                    <CardDescription>悬停卡片组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <Button variant="outline">悬停查看详情</Button>
                      </HoverCardTrigger>
                      <HoverCardContent>
                        <div className="space-y-2">
                          <h4 className="text-sm font-semibold">卡片标题</h4>
                          <p className="text-sm text-gray-500">
                            悬停卡片的详细内容描述
                          </p>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  </CardContent>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Utility Components */}
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="w-8 h-8 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mr-3">
                  6
                </span>
                工具组件
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* ScrollArea */}
                <Card>
                  <CardHeader>
                    <CardTitle>ScrollArea</CardTitle>
                    <CardDescription>滚动区域组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-32 w-full rounded-md border p-4">
                      <div className="space-y-2">
                        <p>可滚动内容 1</p>
                        <p>可滚动内容 2</p>
                        <p>可滚动内容 3</p>
                        <p>可滚动内容 4</p>
                        <p>可滚动内容 5</p>
                        <p>可滚动内容 6</p>
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>

                {/* Separator */}
                <Card>
                  <CardHeader>
                    <CardTitle>Separator</CardTitle>
                    <CardDescription>分隔线组件</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm text-gray-500 mb-2">水平分隔</p>
                      <Separator />
                    </div>
                    <div className="flex items-center space-x-4">
                      <Separator orientation="vertical" className="h-16" />
                      <p className="text-sm text-gray-500">垂直分隔</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Command */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>Command</CardTitle>
                    <CardDescription>命令面板组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => {
                        const dialog = document.getElementById('command-dialog') as HTMLDialogElement
                        dialog?.showModal()
                      }}
                    >
                      打开命令面板 (⌘K)
                    </Button>
                    <dialog id="command-dialog" className="rounded-lg border p-4 shadow-lg">
                      <CommandDialog>
                        <CommandInput placeholder="输入命令..." />
                        <CommandList>
                          <CommandEmpty>没有找到结果</CommandEmpty>
                          <CommandGroup heading="建议">
                            <CommandItem>
                              <Search className="mr-2 h-4 w-4" />
                              <span>搜索</span>
                            </CommandItem>
                            <CommandItem>
                              <Bell className="mr-2 h-4 w-4" />
                              <span>通知</span>
                            </CommandItem>
                          </CommandGroup>
                        </CommandList>
                      </CommandDialog>
                    </dialog>
                  </CardContent>
                </Card>

                {/* Collapsible */}
                <Card>
                  <CardHeader>
                    <CardTitle>Collapsible</CardTitle>
                    <CardDescription>可折叠内容</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Collapsible>
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" className="w-full">
                          <ChevronRight className="h-4 w-4" />
                          展开内容
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-2 space-y-2">
                        <div className="rounded-md border px-4 py-2 text-sm">
                          折叠内容 1
                        </div>
                        <div className="rounded-md border px-4 py-2 text-sm">
                          折叠内容 2
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </CardContent>
                </Card>
              </div>
            </section>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>所有组件基于 shadcn/ui + TailwindCSS 构建</p>
          <p className="mt-1">遵循 Accessible 设计原则，支持键盘导航和屏幕阅读器</p>
        </div>
      </div>
    </div>
  )
}
