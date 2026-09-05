---
outline: [1,3]
tags: [Blazor, C#]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "backend/blazor.md"
---

## 项目开发注意事项

### `BootstrapInput`设置宽度226px

### 查询界面

 - 第一种情况  实体类有设置项，直接使用`BootstrapInput`
 - 第二种情况  实体类没有设置项，使用内联`ShowLabel="true" DisplayText="类别名称：" `

``` csharp
 <div class="right-content mb-3">
         <h6 class="mb-3">基础信息</h6>
     <div class="d-flex align-items-center flex-wrap">

         <div class="d-flex align-items-center mb-3 me-5">
             <BootstrapInput id="device-number" style="width: 226px;" PlaceHolder="请输入 ..." @bind-Value="DevicesItem.DeviceCode" />
         </div>
         <div class="d-flex align-items-center mb-3 me-5">
             <BootstrapInput id="device-name" style="width: 226px;" PlaceHolder="请输入 ..." @bind-Value="DevicesItem.DeviceName" />
         </div>
         <div class="d-flex align-items-center mb-3 me-5">
             <BootstrapInput id="device-model" style="width: 226px;" PlaceHolder="请输入 ..." @bind-Value="DevicesItem.DeviceSpec" />
         </div>
         <div class="d-flex align-items-center mb-3 me-5">
             <Select IsClearable="true" @bind-Value="DevicesItem.DeviceType" PlaceHolder="请选择" style="width: 226px;"></Select>
         </div>
         <div class="d-flex align-items-center mb-3 me-5">
             <BootstrapInput id="mac-address" style="width: 226px;" PlaceHolder="请输入 ..." @bind-Value="DevicesItem.Mac" />
         </div>
         <div class="d-flex align-items-center mb-3 me-5">
             <BootstrapInput id="remark" style="width: 226px;" PlaceHolder="请输入 ..." @bind-Value="DevicesItem.Remark" />
         </div>

     </div>
 </div>


   <div class="d-flex align-items-center mb-3 me-5">
       <BootstrapInput style="width: 226px;" TValue="string" @bind-Value="Search.EventName" ShowLabel="true" DisplayText="事件名称：" />
   </div>

 ```

###  增加、编辑、复制界面

- 使用同级`<label class="form-label">仓库：</label>` ,同时用`required="true"`来控制必填项

``` csharp
 <div class="d-flex align-items-center mb-3 me-5">
     <label class="form-label" required="true">单位名称：</label>
     <BootstrapInput style="width: 226px;" TValue="string" @bind-Value="Record.DealName" />
 </div>
```
 

## blazor传递参数

父组件

``` html
<Main>
    <Breadcrumb Value="@BreadcrumbItem" />
    <CascadingValue Value="this" IsFixed="true">
        @Body
    </CascadingValue>
</Main>
```


``` csharp
[NotNull]
private IEnumerable<BreadcrumbItem> BreadcrumbItem { get; set; }= new List<BreadcrumbItem>();

/// <summary>
/// 子组件传递参数，更新面包屑
/// </summary>
/// <param name="data"></param>
/// <returns></returns>
public async Task UpdateBreadcrumbItem(IEnumerable<BreadcrumbItem> data)
{
    BreadcrumbItem = data;
    StateHasChanged();
    await Task.CompletedTask;
}
```

子组件

``` csharp
   [CascadingParameter]
   private MainLayout Parent { get; set; }
```


